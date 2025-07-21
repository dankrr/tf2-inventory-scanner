(function () {
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

  function getFailedUsers() {
    return [...document.querySelectorAll('.user-card.failed')]
      .filter(div => !div.classList.contains('private'))
      .map(div => div.dataset.steamid);
  }

  function updateFailedCount() {
    const el = document.getElementById('failed-count');
    if (el) el.textContent = getFailedUsers().length;
  }

  function updateRefreshButton() {
    const btn = document.getElementById('refresh-failed-btn');
    if (!btn) return;
    const count = getFailedUsers().length;
    if (count === 0) {
      btn.disabled = true;
      btn.textContent = 'Nothing to Refresh';
      btn.classList.add('btn-disabled');
    } else {
      btn.disabled = false;
      btn.textContent = `Refresh Failed (${count})`;
      btn.classList.remove('btn-disabled');
    }
    updateFailedCount();
  }

  function resetCardForRetry(steamid) {
    const card = document.getElementById('user-' + steamid);
    if (!card) return;

    const banner = card.querySelector('.error-banner');
    if (banner) banner.remove();

    const container = card.querySelector('.inventory-container');
    if (container) container.innerHTML = '';

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

    card.classList.remove('failed', 'success');
    card.classList.add('loading');
  }

  async function retryInventory(id, opts = {}) {
    const { updateButton = true, silent = false } = opts;
    resetCardForRetry(id);

    if (typeof window.startInventoryFetch === 'function') {
      window.startInventoryFetch(id);
    } else if (typeof window.fetchUserCard === 'function') {
      await window.fetchUserCard(id);
      if (!silent) showResults();
    }

    if (updateButton) updateRefreshButton();
  }

  async function refreshAll() {
    const btn = document.getElementById('refresh-failed-btn');
    if (!btn) return;

    const ids = getFailedUsers();
    const total = ids.length;
    if (total === 0) return;

    btn.disabled = true;
    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      btn.textContent = `Refreshing\u2026 (${i + 1} / ${total})`;
      updateScanToast(i + 1, total);
      await retryInventory(id, { updateButton: false, silent: true });
      await new Promise(r => setTimeout(r, 200));
    }

    hideScanToast();
    btn.disabled = false;
    attachHandlers();
    updateRefreshButton();
    updateFailedCount();
  }

  function handleRetryClick(e) {
    const btn = e.currentTarget;
    if (!btn) return;
    retryInventory(btn.dataset.steamid);
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

  function attachHandlers() {
    document.querySelectorAll('.retry-button').forEach(btn => {
      btn.removeEventListener('click', handleRetryClick);
      btn.addEventListener('click', handleRetryClick);
    });
    const refreshBtn = document.getElementById('refresh-failed-btn');
    if (refreshBtn) {
      refreshBtn.removeEventListener('click', refreshAll);
      refreshBtn.addEventListener('click', refreshAll);
    }
    attachItemModal();
    updateRefreshButton();
  }

  document.addEventListener('DOMContentLoaded', () => {
    attachHandlers();
    updateFailedCount();
    if (document.getElementById('user-container').children.length) {
      showResults();
    }
  });

  window.retryInventory = retryInventory;
  window.refreshAll = refreshAll;
  window.attachHandlers = attachHandlers;
  window.updateScanToast = updateScanToast;
  window.hideScanToast = hideScanToast;
  window.updateRefreshButton = updateRefreshButton;
  window.updateFailedCount = updateFailedCount;
})();
