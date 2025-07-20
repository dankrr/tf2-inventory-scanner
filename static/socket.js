
(function () {
  const progressMap = new Map(); // steamid -> { el, bar }
  let socket;

  function initSocket(retry = 0) {
    if (!window.io) {
      if (retry < 5) setTimeout(() => initSocket(retry + 1), 500);
      return;
    }
    socket = io('/inventory', { transports: ['websocket'] });
    window.inventorySocket = socket;

    socket.on('connect', () => console.log('✅ Socket.IO connected'));
    socket.on('connect_error', err => console.error('❌ Socket.IO error:', err));

    registerSocketEvents(socket);
  }

  initSocket();


  function insertProgressBar(steamid) {
    const card = document.getElementById('user-' + steamid);
    if (!card) return;
    let barWrap = card.querySelector('.user-progress');
    let inner;
    if (!barWrap) {
      barWrap = document.createElement('div');
      barWrap.className = 'user-progress';
      inner = document.createElement('div');
      inner.className = 'progress-inner';
      inner.id = 'progress-' + steamid;
      barWrap.appendChild(inner);
      card.appendChild(barWrap);
    } else {
      inner = barWrap.querySelector('.progress-inner');
    }
    progressMap.set(String(steamid), { el: barWrap, bar: inner });
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
      '</div><div class="card-body"><div class="inventory-container"></div></div>';
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
  
  function registerSocketEvents(s) {

    s.on('info', data => {
    let p = progressMap.get(String(data.steamid));
    if (!p) {
      insertProgressBar(data.steamid);
      p = progressMap.get(String(data.steamid));
    }
    if (p) {
      p.bar.style.width = '0%';
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
      p.bar.style.width = pct + '%';
      // force reflow so transition animates
      void p.bar.offsetWidth;
      p.bar.textContent = `${data.processed}/${data.total}`;
    });

    s.on('item', data => {
    const container = document.querySelector(`#user-${data.steamid} .inventory-container`);
    if (!container) return;
    const frag = document.createDocumentFragment();
    const el = createItemElement(data);
    frag.appendChild(el);
    container.appendChild(frag);
    if (window.attachItemModal) {
      window.attachItemModal();
    } else if (window.attachHandlers) {
      window.attachHandlers();
    }
    if (window.refreshLazyLoad) {
      window.refreshLazyLoad();
    }
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
      p.bar.textContent = data.status === 'parsed' ? 'Done' : 'Failed';
      setTimeout(() => {
        p.el.classList.add('fade-out');
        setTimeout(() => p.el.remove(), 600);
      }, 4000);
      progressMap.delete(String(data.steamid));
    }
  });

  }

  window.startInventoryFetch = function (steamid) {
    if (!socket || socket.disconnected) {
      console.warn('⚠ Socket not ready, using fallback API.');
      fetchUserCard(steamid);
      return;
    }
    insertProgressBar(steamid);
    socket.emit('start_fetch', { steamid });
  };
})();
