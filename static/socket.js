

(function () {
  const progressMap = new Map(); // steamid -> { el, bar, eta }
  const itemQueue = [];
  let queueHandle = null;
  const scheduler = window.requestIdleCallback
    ? { run: cb => requestIdleCallback(cb), cancel: handle => cancelIdleCallback(handle) }
    : { run: cb => requestAnimationFrame(cb), cancel: handle => cancelAnimationFrame(handle) };
  let domBatchSize = window.innerWidth > 1024 ? 30 : 10;
  let socket;
  let reconnectDelay = 500;
  let pendingSubmission = null;

  function processQueue() {
    queueHandle = null;
    if (!itemQueue.length) return;
    const start = performance.now();
    const batch = itemQueue.splice(0, domBatchSize);
    const fragMap = new Map();
    batch.forEach(({ container, el }) => {
      let frag = fragMap.get(container);
      if (!frag) {
        frag = document.createDocumentFragment();
        fragMap.set(container, frag);
      }
      frag.appendChild(el);
    });
    fragMap.forEach((frag, container) => {
      container.appendChild(frag);
      if (frag.firstChild) void frag.firstChild.offsetHeight;
    });
    if (window.attachItemModal) {
      window.attachItemModal();
    } else if (window.attachHandlers) {
      window.attachHandlers();
    }
    if (window.refreshLazyLoad) window.refreshLazyLoad();
    const frameTime = performance.now() - start;
    console.log(`Processed batch of ${batch.length}, remaining: ${itemQueue.length}`);
    if (frameTime < 10 && domBatchSize < 100) {
      domBatchSize += 5;
      console.debug('⚡ DOM batch ->', domBatchSize);
    } else if (frameTime > 20 && domBatchSize > 10) {
      domBatchSize = Math.max(10, domBatchSize - 5);
      console.debug('🐢 DOM batch ->', domBatchSize);
    }
    console.debug('Queue length:', itemQueue.length, 'Batch size:', domBatchSize);
    if (itemQueue.length) {
      queueHandle = scheduler.run(processQueue);
    }
  }

  function enqueueItem(container, el, steamid) {
    itemQueue.push({ container, el, steamid: String(steamid) });
    console.log('Queue length after enqueue:', itemQueue.length);
    if (!queueHandle) {
      queueHandle = scheduler.run(processQueue);
    }
  }

  function removeQueued(id) {
    const sid = String(id);
    for (let i = itemQueue.length - 1; i >= 0; i--) {
      if (itemQueue[i].steamid === sid) {
        itemQueue.splice(i, 1);
      }
    }
    if (!itemQueue.length && queueHandle) {
      scheduler.cancel(queueHandle);
      queueHandle = null;
    }
  }

  function flushQueued(id) {
    const sid = String(id);
    const fragMap = new Map();
    for (let i = itemQueue.length - 1; i >= 0; i--) {
      if (itemQueue[i].steamid === sid) {
        const { container, el } = itemQueue.splice(i, 1)[0];
        let frag = fragMap.get(container);
        if (!frag) {
          frag = document.createDocumentFragment();
          fragMap.set(container, frag);
        }
        frag.appendChild(el);
      }
    }
    fragMap.forEach((frag, container) => {
      container.appendChild(frag);
      if (frag.firstChild) void frag.firstChild.offsetHeight;
    });
    if (!itemQueue.length && queueHandle) {
      scheduler.cancel(queueHandle);
      queueHandle = null;
    }
  }

  function drainQueue() {
    while (itemQueue.length) {
      processQueue();
    }
    if (queueHandle) {
      scheduler.cancel(queueHandle);
      queueHandle = null;
    }
  }


  function retryConnect() {
    setTimeout(initSocket, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 10000);
  }

  function initSocket() {
    if (!window.io) {
      setTimeout(initSocket, 500);
      return;
    }

    socket = io('/inventory', { transports: ['websocket'] });
    window.inventorySocket = socket;
    const btn = document.getElementById('check-inventory-btn');
    if (btn) btn.disabled = true;

    socket.on('connect', () => {
      console.log('✅ Socket.IO connected via', socket.io.engine.transport.name);
      reconnectDelay = 500;
      if (window.enableSubmitButton) window.enableSubmitButton();
      if (Array.isArray(pendingSubmission)) {
        const ids = pendingSubmission;
        pendingSubmission = null;
        ids.forEach(id => window.startInventoryFetch(id));
      }
    });

    socket.on('disconnect', () => {
      console.warn('Socket.IO disconnected');
      const btn = document.getElementById('check-inventory-btn');
      if (btn) btn.disabled = true;
      if (queueHandle) {
        scheduler.cancel(queueHandle);
        queueHandle = null;
      }
      itemQueue.length = 0;
      retryConnect();
    });

    socket.on('connect_error', err => {
      console.error('❌ Socket.IO error:', err);
    });

    registerSocketEvents(socket);
  }

  initSocket();


  function insertProgressBar(steamid) {
    const card = document.getElementById('user-' + steamid);
    if (!card) return;
    let barWrap = card.querySelector('.user-progress');
    let inner;
    let eta;
    if (!barWrap) {
      barWrap = document.createElement('div');
      barWrap.className = 'user-progress';
      inner = document.createElement('div');
      inner.className = 'progress-inner';
      inner.id = 'progress-' + steamid;
      eta = document.createElement('span');
      eta.className = 'eta-label';
      eta.id = 'eta-' + steamid;
      barWrap.appendChild(inner);
      barWrap.appendChild(eta);
      card.appendChild(barWrap);
    } else {
      inner = barWrap.querySelector('.progress-inner');
      eta = barWrap.querySelector('.eta-label');
      barWrap.classList.remove('fade-out');
    }
    inner.style.width = '0%';
    // reset transition start point
    void inner.offsetWidth;
    progressMap.set(String(steamid), { el: barWrap, bar: inner, eta });
  }

  function clearExisting(steamid) {
    const card = document.getElementById('user-' + steamid);
    if (!card) return;
    const container = card.querySelector('.inventory-container');
    if (container) container.innerHTML = '';
    const bar = card.querySelector('.user-progress');
    if (bar) bar.remove();
    progressMap.delete(String(steamid));
    removeQueued(steamid);
  }

  function insertUserPlaceholder(id) {
    const container = document.getElementById('user-container');
    if (!container || document.getElementById('user-' + id)) return;
    const div = document.createElement('div');
    div.id = 'user-' + id;
    div.className = 'user-card loading';
    div.innerHTML =
      '<div class="card-header">' +
      id +
      '<div class="header-right"><button class="cancel-btn" type="button" onclick="cancelInventoryFetch(' +
      id +
      ')">&#x2716;</button></div></div><div class="card-body"><div class="inventory-container"></div></div>';
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    div.appendChild(spinner);
    const barWrap = document.createElement('div');
    barWrap.className = 'user-progress';
    const inner = document.createElement('div');
    inner.className = 'progress-inner';
    inner.id = 'progress-' + id;
    barWrap.appendChild(inner);
    div.appendChild(barWrap);
    container.appendChild(div);
  }

  function createBadge(badge, data) {
    if (badge.type === 'statclock' || badge.icon === '\u{1f3a8}') {
      return null;
    }
    if (badge.type === 'killstreak') {
      const span = document.createElement('span');
      span.className = 'badge';
      span.dataset.icon = badge.icon;
      span.title = badge.title || '';
      const icon = document.createElement('span');
      icon.className = 'chevron-icon';
      if (data.sheen_gradient_css) {
        icon.style.cssText = `${data.sheen_gradient_css}; -webkit-background-clip:text; background-clip:text; color:transparent;`;
      } else if (data.sheen_color) {
        icon.style.color = data.sheen_color;
      }
      icon.textContent = badge.icon;
      span.appendChild(icon);
      return span;
    }
    if (badge.icon_url) {
      const img = document.createElement('img');
      img.className = 'badge-icon';
      img.loading = 'lazy';
      img.dataset.src = badge.icon_url;
      img.alt = '';
      if (badge.title) img.title = badge.title;
      return img;
    }
    const span = document.createElement('span');
    span.className = 'badge';
    span.dataset.icon = badge.icon;
    if (badge.color) span.style.color = badge.color;
    if (badge.title) span.title = badge.title;
    span.textContent = badge.icon;
    return span;
  }

  function createItemElement(data) {
    const wrapper = document.createElement('div');
    wrapper.className = 'item-wrapper fade-in-item';

    const card = document.createElement('div');
    card.className = 'item-card';
    if (data.untradable_hold) card.classList.add('trade-hold');
    if (data.uncraftable) card.classList.add('uncraftable');
    if (data.has_strange_tracking) card.classList.add('elevated-strange');
    card.style.setProperty('--quality-color', data.quality_color || '#b2b2b2');
    if (data.border_color || data.quality_color) {
      card.style.borderColor = data.border_color || data.quality_color;
    }
    if (data.has_strange_tracking) card.title = 'Has Strange tracking';
    card.dataset.item = JSON.stringify(data);
    card.dataset.craftable = data.craftable ? 'true' : 'false';

    const badges = document.createElement('div');
    badges.className = 'item-badges';
    if (data.is_australium) {
      const img = document.createElement('img');
      img.className = 'australium-icon';
      img.loading = 'lazy';
      img.dataset.src = '/static/images/logos/australium.png';
      img.alt = 'Australium';
      badges.appendChild(img);
    }
    if (data.paint_hex) {
      const dot = document.createElement('span');
      dot.className = 'paint-dot';
      dot.style.backgroundColor = data.paint_hex;
      if (data.paint_name) dot.title = 'Paint: ' + data.paint_name;
      badges.appendChild(dot);
    }
    if (Array.isArray(data.badges)) {
      data.badges.forEach(b => {
        const el = createBadge(b, data);
        if (el) badges.appendChild(el);
      });
    }
    card.appendChild(badges);

    if (data.quantity && data.quantity > 1) {
      const qty = document.createElement('span');
      qty.className = 'item-qty';
      qty.textContent = 'x' + data.quantity;
      card.appendChild(qty);
    }

    if (data.statclock_badge) {
      const img = document.createElement('img');
      img.className = 'statclock-badge';
      img.loading = 'lazy';
      img.dataset.src = data.statclock_badge;
      img.alt = 'StatTrak\u2122';
      img.title = 'StatTrak\u2122 Active';
      card.appendChild(img);
    }

    if (data.unusual_effect_id) {
      const effect = document.createElement('img');
      effect.className = 'particle-bg';
      effect.loading = 'lazy';
      effect.dataset.src = `/static/images/effects/${data.unusual_effect_id}.png`;
      effect.alt = 'effect';
      card.appendChild(effect);
    }

    if (data.target_weapon_image) {
      const kit = document.createElement('div');
      kit.className = 'kit-composite';
      const bg = document.createElement('img');
      bg.className = 'kit-bg';
      bg.loading = 'lazy';
      bg.dataset.src = data.image_url;
      bg.width = 96;
      bg.height = 96;
      bg.alt = data.display_name || data.name || 'Item';
      kit.appendChild(bg);
      const overlay = document.createElement('img');
      overlay.className = 'kit-weapon-overlay';
      overlay.loading = 'lazy';
      overlay.dataset.src = data.target_weapon_image;
      overlay.alt = 'overlay';
      kit.appendChild(overlay);
      card.appendChild(kit);
    } else if (data.image_url) {
      const img = document.createElement('img');
      img.className = 'item-img';
      img.loading = 'lazy';
      img.dataset.src = data.image_url;
      img.alt = data.display_name || data.name || 'Item';
      img.width = 64;
      img.height = 64;
      img.onerror = () => {
        img.style.display = 'none';
      };
      card.appendChild(img);
    } else {
      const missing = document.createElement('div');
      missing.className = 'missing-icon';
      card.appendChild(missing);
    }

    const nameDiv = document.createElement('div');
    nameDiv.className = 'item-name';
    nameDiv.textContent = data.display_name || data.name || 'Item';
    card.appendChild(nameDiv);

    wrapper.appendChild(card);

    const price = document.createElement('div');
    price.className = 'item-price';
    price.textContent = 'Price: ' + (data.formatted_price || 'N/A');
    wrapper.appendChild(price);

    setTimeout(() => wrapper.classList.add('show'), 10);
    return wrapper;
  }
  
  function registerSocketEvents(s) {

    s.on('info', data => {
      const card = document.getElementById('user-' + data.steamid);
      if (card) {
        const header = card.querySelector('.card-header');
        if (header) {
          const avatar = data.avatar || '/static/images/logos/tf2autobot.png';
          const username = data.username || data.steamid;
          const profile = data.profile || `https://steamcommunity.com/profiles/${data.steamid}`;
          const backpack = data.backpack || `https://next.backpack.tf/profiles/${data.steamid}`;
          const playtime = data.playtime ?? 0;
          header.innerHTML = `
            <div class="user-header">
              <div class="user-profile">
                <a href="${profile}" target="_blank" class="avatar-link">
                  <img src="${avatar}" alt="Avatar" class="profile-pic" loading="lazy"/>
                </a>
                <div class="profile-details">
                  <div class="username">${username}</div>
                  <div class="tf2-hours">TF2 Playtime: ${playtime} hrs</div>
                  <div class="profile-link">
                    <a href="${backpack}" class="backpack-link" target="_blank" rel="noopener">
                      Backpack.tf
                      <img src="/static/images/logos/bptf_small.PNG" alt="Backpack.tf" class="inline-icon"/>
                    </a>
                  </div>
                </div>
              </div>
              <div class="header-right">
                <button class="cancel-btn" type="button" onclick="cancelInventoryFetch(${data.steamid})">&#x2716;</button>
              </div>
            </div>`;
        }
        const invContainer = card.querySelector('.inventory-container');
        if (invContainer && !card.querySelector('.inventory-scroll')) {
          const scrollWrapper = document.createElement('div');
          scrollWrapper.className = 'inventory-scroll';
          const leftBtn = document.createElement('button');
          leftBtn.className = 'scroll-arrow left';
          leftBtn.innerHTML = '<i class="fa-solid fa-chevron-left"></i>';
          const rightBtn = document.createElement('button');
          rightBtn.className = 'scroll-arrow right';
          rightBtn.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
          scrollWrapper.appendChild(leftBtn);
          scrollWrapper.appendChild(invContainer);
          scrollWrapper.appendChild(rightBtn);
          const body = card.querySelector('.card-body');
          if (body) body.appendChild(scrollWrapper);
        }
      }
      let p = progressMap.get(String(data.steamid));
      if (!p) {
        insertProgressBar(data.steamid);
        p = progressMap.get(String(data.steamid));
      }
      if (p) {
        p.bar.style.width = '0%';
        // force reflow to restart transition
        void p.bar.offsetWidth;
        p.bar.textContent = `0/${data.total || 0}`;
      }
    });


    s.on('progress', data => {
      const p = progressMap.get(String(data.steamid));
      if (!p) return;
      const card = document.getElementById('user-' + data.steamid);
      if (card) {
        const spin = card.querySelector('.loading-spinner');
        if (spin) spin.remove();
      }
      const pct = Math.min((data.processed / data.total) * 100, 100);
      void p.bar.offsetWidth;
      p.bar.style.width = pct + '%';
      p.bar.textContent = `${data.processed}/${data.total}`;
      if (p.eta) {
        if (data.eta && data.eta > 0) {
          p.eta.textContent = `~${data.eta}s remaining`;
        } else {
          p.eta.textContent = '';
        }
      }
      console.debug(
        `Progress: ${data.processed}/${data.total}, ETA: ${data.eta}s`
      );
    });

    s.on('items_batch', data => {
      const container = document.querySelector(
        `#user-${data.steamid} .inventory-container`
      );
      if (!container) {
        console.error('Container not found for', data.steamid);
        return;
      }
      const batch = data.items || [];
      console.log(`📦 Received ${batch.length} items for ${data.steamid}`);
      if (batch.length) console.log('Sample item:', batch[0]);
      batch.forEach(item => {
        const el = createItemElement(item);
        enqueueItem(container, el, data.steamid);
      });
      console.debug(
        `📦 Received batch of ${batch.length}, remaining approx: ${itemQueue.length}`
      );
      if (window.DEBUG_FORCE_RENDER) drainQueue();
    });

    s.on('done', data => {
    const card = document.getElementById('user-' + data.steamid);
    if (card) {
      card.classList.remove('loading');
      const spin = card.querySelector('.loading-spinner');
      if (spin) spin.remove();

      const header = card.querySelector('.card-header');
      if (header) {
        let pill = header.querySelector('.status-pill');
        if (!pill) {
          pill = document.createElement('span');
          pill.className = 'status-pill';
          header.appendChild(pill);
        }
        if (data.status === 'parsed') {
          pill.className = 'status-pill parsed';
          pill.innerHTML = '<i class="fa-solid fa-check"></i>';
        } else {
          pill.className = 'status-pill failed';
          pill.innerHTML = '<i class="fa-solid fa-xmark"></i>';

          // ✅ Add Retry Button if not already present
          let retryBtn = header.querySelector('.retry-button');
          if (!retryBtn) {
            retryBtn = document.createElement('button');
            retryBtn.className = 'pill status-pill failed retry-button';
            retryBtn.type = 'button';
            retryBtn.setAttribute('aria-label', 'Retry scan for this user');
            retryBtn.innerHTML =
              '<i class="fa-solid fa-arrows-rotate"></i> Retry';
            header.appendChild(retryBtn);
          }
          // ensure steamid dataset is set correctly
          retryBtn.dataset.steamid = String(data.steamid);
        }
      }

      if (data.status !== 'parsed') {
        const body = card.querySelector('.card-body');
        if (body && !card.querySelector('.error-banner')) {
          const msg = document.createElement('div');
          msg.className = 'error-banner';
          msg.textContent =
            data.status === 'private'
              ? 'Inventory private'
              : data.status === 'timeout'
              ? 'Timed out'
              : 'Inventory unavailable';
          body.insertBefore(msg, body.firstChild);
        }
      } else {
        const container = card.querySelector('.inventory-container');
        if (container && !card.querySelector('.sort-value-btn')) {
          const body = card.querySelector('.card-body');
          if (body) {
            const btn = document.createElement('button');
            btn.className = 'sort-value-btn';
            btn.type = 'button';
            btn.textContent = 'Sort by Value';
            btn.addEventListener('click', () => {
              const wrappers = Array.from(
                container.querySelectorAll('.item-wrapper')
              );
              wrappers.sort((a, b) => {
                const da = a.querySelector('.item-card')?.dataset.item;
                const db = b.querySelector('.item-card')?.dataset.item;
                let va = 0;
                let vb = 0;
                if (da) {
                  try {
                    va = JSON.parse(da).price?.value_raw || 0;
                  } catch (e) {}
                }
                if (db) {
                  try {
                    vb = JSON.parse(db).price?.value_raw || 0;
                  } catch (e) {}
                }
                return vb - va;
              });
              wrappers.forEach(w => container.appendChild(w));
            });
            body.insertBefore(btn, body.firstChild);
          }
        }
      }
    }

    const p = progressMap.get(String(data.steamid));
    if (p) {
      p.bar.style.width = '100%';
      // ensure final width transition flushes
      void p.bar.offsetWidth;
      p.bar.textContent = data.status === 'parsed' ? 'Done' : 'Failed';
      if (p.eta) p.eta.textContent = '';
      setTimeout(() => {
        p.el.classList.add('fade-out');
        setTimeout(() => p.el.remove(), 600);
      }, 4000);
      progressMap.delete(String(data.steamid));
      flushQueued(data.steamid);
      drainQueue();
      const cancelBtn = card.querySelector('.cancel-btn');
      if (cancelBtn) cancelBtn.disabled = true;
    }
  });

  }

  window.startInventoryFetch = function (steamid) {
    if (!socket || socket.disconnected) {
      console.warn('⚠ Socket not ready, queuing fetch');
      if (!pendingSubmission) pendingSubmission = [];
      if (!pendingSubmission.includes(String(steamid))) {
        pendingSubmission.push(String(steamid));
      }
      return;
    }
    clearExisting(steamid);
    insertProgressBar(steamid);
    socket.emit('start_fetch', { steamid });
  };

  window.cancelInventoryFetch = function (steamid) {
    if (socket) socket.emit('cancel_fetch', { steamid });
    removeQueued(steamid);
    const card = document.getElementById('user-' + steamid);
    if (card) {
      card.classList.add('fade-out');
      setTimeout(() => card.remove(), 600);
    }
    const p = progressMap.get(String(steamid));
    if (p && p.el) p.el.remove();
    progressMap.delete(String(steamid));
    if (!itemQueue.length && queueHandle) {
      scheduler.cancel(queueHandle);
      queueHandle = null;
    }
  };

  window._debugQueue = itemQueue;
  window._debugProcessQueue = processQueue;
  window.DEBUG_FORCE_RENDER = false;

  document.addEventListener('click', e => {
    const left = e.target.closest('.scroll-arrow.left');
    if (left) {
      const container = left.closest('.inventory-scroll')?.querySelector('.inventory-container');
      if (container) container.scrollBy({ left: -200, behavior: 'smooth' });
    }
    const right = e.target.closest('.scroll-arrow.right');
    if (right) {
      const container = right.closest('.inventory-scroll')?.querySelector('.inventory-container');
      if (container) container.scrollBy({ left: 200, behavior: 'smooth' });
    }
  });

  document.addEventListener('click', e => {
    const retryBtn = e.target.closest('.retry-button');
    if (!retryBtn) return;
    const steamid = retryBtn.dataset.steamid;
    if (!steamid) return;

    console.log(`\u{1F501} Retrying inventory fetch for ${steamid}`);

    const card = document.getElementById('user-' + steamid);
    if (card) {
      const errorBanner = card.querySelector('.error-banner');
      if (errorBanner) errorBanner.remove();

      const invContainer = card.querySelector('.inventory-container');
      if (invContainer) invContainer.innerHTML = '';

      let spinner = card.querySelector('.loading-spinner');
      if (!spinner) {
        spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.setAttribute('aria-label', 'Loading');
        card.appendChild(spinner);
      }

      const bar = card.querySelector('.progress-inner');
      if (bar) {
        bar.style.width = '0%';
        bar.textContent = '0';
      }

      card.classList.add('loading');
    }

    if (typeof window.startInventoryFetch === 'function') {
      window.startInventoryFetch(steamid);
    } else {
      console.error('startInventoryFetch is not defined');
    }
  });
})();
