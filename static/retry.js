function appendCard(html) {
  const wrapper = document.createElement('div');
  wrapper.innerHTML = html;
  const card = wrapper.firstElementChild;
  if (card) {
    document.getElementById('user-container').appendChild(card);
    showResults();
  }
}

function updateScanToast(current, total) {
  const toast = document.getElementById('scan-toast');
  if (!toast) return;
  toast.textContent = `\u{1F504} Scanning ${current} of ${total} inventories...`;
  toast.classList.remove('hidden');
  toast.classList.add('show');
}

function hideScanToast() {
  const toast = document.getElementById('scan-toast');
  if (!toast) return;
  toast.classList.remove('show');
  setTimeout(() => toast.classList.add('hidden'), 300);
}

let pendingIDs = [];
let loadingNext = false;

function lazyLoadNext() {
  if (loadingNext || !pendingIDs.length) return;
  loadingNext = true;
  const id = pendingIDs.shift();
  let card = document.querySelector('[data-steamid="' + id + '"]');
  if (!card) {
    card = document.createElement('div');
    card.id = 'user-' + id;
    card.dataset.steamid = id;
    card.className = 'user-card user-box loading';
    document.getElementById('user-container').appendChild(card);
  } else {
    card.classList.remove('failed', 'success');
    card.classList.add('loading');
    card.innerHTML = '';
  }
  updateScanToast(window.initialIds.length - pendingIDs.length, window.initialIds.length);
  fetch('/retry/' + id, { method: 'POST' })
    .then(r => r.text())
    .then(html => {
      const wrapper = document.createElement('div');
      wrapper.innerHTML = html;
      const newCard = wrapper.firstElementChild;
      if (newCard) {
        card.replaceWith(newCard);
      }
      streamInventory(id);
      attachHandlers();
      updateRefreshButton();
      showResults();
    })
    .catch(() => {
      const existing = document.getElementById('user-' + id);
      if (existing) {
        existing.classList.remove('loading');
        existing.classList.add('failed');
      }
      updateRefreshButton();
    })
    .finally(() => {
      loadingNext = false;
      if (!pendingIDs.length) {
        hideScanToast();
      }
    });
}

function retryInventory(id) {
  let card = document.querySelector('[data-steamid="' + id + '"]');
  if (card) {
    card.classList.remove('failed', 'success');
    card.classList.add('loading');
    card.innerHTML = '';
  } else {
    card = document.createElement('div');
    card.id = 'user-' + id;
    card.dataset.steamid = id;
    card.className = 'user-card user-box loading';
    document.getElementById('user-container').appendChild(card);
  }

  const pill = card.querySelector('.status-pill');
  if (pill) {
    pill.innerHTML = '<i class="fa-solid fa-arrows-rotate fa-spin"></i>';
  }

  return fetch('/retry/' + id, { method: 'POST' })
    .then(r => r.text())
    .then(html => {
      const wrapper = document.createElement('div');
      wrapper.innerHTML = html;
      const newCard = wrapper.firstElementChild;
      if (newCard) {
        card.replaceWith(newCard);
      }
      streamInventory(id);
      attachHandlers();
      updateRefreshButton();
      showResults();
    })
    .catch(() => {
      const existing = document.getElementById('user-' + id);
      if (existing) {
        existing.classList.remove('loading');
        existing.classList.add('failed');
      }
      updateRefreshButton();
    });
}

function streamInventory(id) {
  const es = new EventSource('/inventory_chunk/' + id);
  es.addEventListener('chunk', e => {
    const card = document.getElementById('user-' + id);
    if (!card) return;
    let container = card.querySelector('.inventory-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'inventory-container';
      card.textContent = '';
      card.appendChild(container);
    }
    container.insertAdjacentHTML('beforeend', e.data);
    attachItemModal();
  });
  es.addEventListener('done', () => {
    es.close();
  });
}

function updateRefreshButton() {
  const btn = document.getElementById('refresh-failed-btn');
  if (!btn) return;
  const failures = document.querySelectorAll('.user-box.failed').length;
  if (failures === 0) {
    btn.disabled = true;
    btn.textContent = 'Nothing to Refresh';
    btn.classList.add('btn-disabled');
  } else {
    btn.disabled = false;
    btn.textContent = `Refresh Failed (${failures})`;
    btn.classList.remove('btn-disabled');
  }
}

document.addEventListener('DOMContentLoaded', updateRefreshButton);

function attachHandlers() {
  document.querySelectorAll('.retry-pill').forEach(el => {
    el.addEventListener('click', () => retryInventory(el.dataset.steamid));
  });
  updateRefreshButton();

  attachItemModal();
}

function refreshAll() {
  const btn = document.getElementById('refresh-failed-btn');
  if (!btn) return;
  btn.disabled = true;
  const original = btn.textContent;
  btn.textContent = 'Refreshing…';
  const failedCards = Array.from(document.querySelectorAll('.user-box.failed'));
  const ids = failedCards.map(el => el.dataset.steamid);
  failedCards.forEach(card => {
    card.innerHTML = '';
    card.classList.remove('failed', 'success');
    card.classList.add('loading');
  });
  pendingIDs.push(...ids);
  btn.disabled = false;
  btn.textContent = original;
  lazyLoadNext();
}

function loadUsers(ids) {
  pendingIDs.push(...ids);
  lazyLoadNext();
}

function showResults() {
  const results = document.getElementById('results');
  if (!results) return;
  results.classList.add('fade-in');
  setTimeout(() => {
    results.classList.add('show');
  }, 10);
}

function initImageObserver() {
  if (!('IntersectionObserver' in window)) return;
  const cached = new Set();
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const img = entry.target;
      const src = img.getAttribute('data-src');
      if (!src) return;
      if (!img.getAttribute('src')) {
        img.src = src;
      }
      if (!cached.has(src)) {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'image';
        link.href = src;
        document.head.appendChild(link);
        cached.add(src);
      }
      observer.unobserve(img);
    });
  }, { rootMargin: '300px' });
  document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
}

function initLazyLoader() {
  const sentinel = document.getElementById('lazy-load-sentinel');
  if (!sentinel) return;
  if (!('IntersectionObserver' in window)) {
    if (pendingIDs.length) lazyLoadNext();
    return;
  }
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        lazyLoadNext();
      }
    });
  });
  observer.observe(sentinel);
}

function attachItemModal() {
  document.querySelectorAll('.item-card').forEach(card => {
    card.addEventListener('click', () => {
      let data = card.dataset.item;
      if (!data) return;
      try {
        data = JSON.parse(data);
      } catch (e) {
        return;
      }
      if (window.modal && typeof window.modal.updateHeader === 'function') {
        window.modal.updateHeader(data);
      }
      if (window.modal && typeof window.modal.setParticleBackground === 'function') {
        window.modal.setParticleBackground(data.unusual_effect_id);
      }
      if (window.modal && typeof window.modal.preloadEffect === 'function') {
        window.modal.preloadEffect(data.unusual_effect_id || data.taunt_effect_id);
      }
      if (window.modal && typeof window.modal.generateModalHTML === 'function') {
        const html = window.modal.generateModalHTML(data);
        if (window.modal.showItemModal) {
          window.modal.showItemModal(html);
        }
      }
      if (window.modal && typeof window.modal.renderBadges === 'function') {
        window.modal.renderBadges(data.badges);
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  attachHandlers();
  const btn = document.getElementById('refresh-failed-btn');
  if (btn) {
    btn.addEventListener('click', refreshAll);
  }
  if (window.initialIds && window.initialIds.length) {
    pendingIDs = window.initialIds.slice();
  }
  initLazyLoader();
  lazyLoadNext();
  attachItemModal();
  initImageObserver();
  if (window.modal && typeof window.modal.initModal === 'function') {
    window.modal.initModal();
  }
  if (document.getElementById('user-container').children.length) {
    showResults();
  }
});
