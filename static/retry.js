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

function resetCardForRetry(steamid) {
  const card = document.getElementById('user-' + steamid);
  if (!card) return;
  card.classList.remove('failed', 'success', 'retry-card');
  card.classList.add('loading');

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
}

function retryInventory(id, updateButton = true) {
  let card = document.getElementById('user-' + id);
  if (!card) {
    card = document.createElement('div');
    card.id = 'user-' + id;
    card.dataset.steamid = id;
    card.className = 'user-card user-box loading';
    document.getElementById('user-container').appendChild(card);
  }

  resetCardForRetry(id);

  const pill = card.querySelector('.status-pill');
  if (pill) {
    pill.innerHTML = '<i class="fa-solid fa-arrows-rotate fa-spin"></i>';
  }

  if (typeof window.startInventoryFetch === 'function') {
    window.startInventoryFetch(id);
    attachHandlers(updateButton);
    if (updateButton) updateRefreshButton();
    return Promise.resolve();
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
      attachHandlers(updateButton);
      if (window.refreshLazyLoad) {
        window.refreshLazyLoad();
      }
      if (updateButton) updateRefreshButton();
      showResults();
    })
    .catch(() => {
      const existing = document.getElementById('user-' + id);
      if (existing) {
        existing.classList.remove('loading');
        existing.classList.add('failed');
      }
      if (updateButton) updateRefreshButton();
    });
}

function getFailedUsers() {
  return [...document.querySelectorAll('.user-card.failed')]
    .filter(div => !div.classList.contains('private'))
    .map(div => div.dataset.steamid);
}

function updateFailedCount() {
  const countEl = document.getElementById('failed-count');
  if (countEl) {
    countEl.textContent = getFailedUsers().length;
  }
}

function updateRefreshButton() {
  const btn = document.getElementById('refresh-failed-btn');
  if (!btn) return;
  const failures = getFailedUsers().length;
  if (failures === 0) {
    btn.disabled = true;
    btn.textContent = 'Nothing to Refresh';
    btn.classList.add('btn-disabled');
  } else {
    btn.disabled = false;
    btn.textContent = `Refresh Failed (${failures})`;
    btn.classList.remove('btn-disabled');
  }
  updateFailedCount();
}


function handleRetryClick(event) {
  const btn = event.currentTarget;
  if (!btn) return;
  retryInventory(btn.dataset.steamid);
}

function attachHandlers(updateButton = true) {
  document.querySelectorAll('.retry-button').forEach(btn => {
    btn.removeEventListener('click', handleRetryClick);
    btn.addEventListener('click', handleRetryClick);
  });
  if (updateButton) {
    updateRefreshButton();
  }

  attachItemModal();
}

async function refreshAll() {
  const btn = document.getElementById('refresh-failed-btn');
  if (!btn) return;
  btn.disabled = true;
  const original = btn.textContent;
  btn.textContent = 'Refreshing…';
  const ids = getFailedUsers();
  const total = ids.length;
  let current = 0;

  for (const id of ids) {
    current += 1;
    updateScanToast(current, total);
    resetCardForRetry(id);
    if (typeof window.startInventoryFetch === 'function') {
      window.startInventoryFetch(id);
      attachHandlers(false);
    } else {
      await retryInventory(id, false);
    }
    await new Promise(r => setTimeout(r, 200));
  }

  hideScanToast();
  btn.disabled = false;
  btn.textContent = original;
  attachHandlers(false);
  updateRefreshButton();
}


function showResults() {
  const results = document.getElementById('results');
  if (!results) return;
  results.classList.add('fade-in');
  setTimeout(() => {
    results.classList.add('show');
  }, 10);
}

function handleItemClick(event) {
  const card = event.currentTarget || event;
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
  if (window.modal && typeof window.modal.generateModalHTML === 'function') {
    const html = window.modal.generateModalHTML(data);
    if (window.modal.showItemModal) {
      window.modal.showItemModal(html);
    }
  }
  if (window.modal && typeof window.modal.renderBadges === 'function') {
    window.modal.renderBadges(data.badges);
  }
}

function attachItemModal() {
  const container = document.getElementById('user-container');
  if (!container) return;
  container.querySelectorAll('.item-card').forEach(card => {
    if (card.dataset.handler) return;
    card.dataset.handler = 'true';
    card.addEventListener('click', handleItemClick);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  attachHandlers();
  const btn = document.getElementById('refresh-failed-btn');
  if (btn) {
    btn.addEventListener('click', refreshAll);
  }
  updateRefreshButton();
  updateFailedCount();
  if (window.modal && typeof window.modal.initModal === 'function') {
    window.modal.initModal();
  }
  if (document.getElementById('user-container').children.length) {
    showResults();
  }
});
