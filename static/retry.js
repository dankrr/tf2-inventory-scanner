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

function showToast(message) {
  const toast = document.getElementById('scan-toast');
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove('hidden');
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.classList.add('hidden'), 300);
  }, 3000);
}

function extractSteamIds(text) {
  const tokens = String(text || '')
    .trim()
    .split(/\s+/);
  const ids = [];
  const seen = new Set();
  const id2 = /^STEAM_0:[01]:\d+$/;
  const id3 = /^\[U:1:\d+\]$/;
  const id64 = /^\d{17}$/;
  tokens.forEach(t => {
    if (!t) return;
    if (id2.test(t) || id3.test(t) || id64.test(t)) {
      if (!seen.has(t)) {
        seen.add(t);
        ids.push(t);
      }
    }
  });
  return ids;
}

function convertToSteam64(id) {
  if (/^\d{17}$/.test(id)) return id;
  if (id.startsWith('STEAM_')) {
    const parts = id.split(':');
    if (parts.length === 3) {
      const y = parseInt(parts[1].split('_')[1] || parts[1], 10);
      const z = parseInt(parts[2], 10);
      if (!Number.isNaN(y) && !Number.isNaN(z)) {
        const accountId = z * 2 + y;
        return String(accountId + 76561197960265728);
      }
    }
  }
  let m = id.match(/^\[U:(\d+):(\d+)\]$/);
  if (m) {
    const z = parseInt(m[2], 10);
    if (!Number.isNaN(z)) return String(z + 76561197960265728);
  }
  m = id.match(/^\[U:1:(\d+)\]$/);
  if (m) {
    const z = parseInt(m[1], 10);
    if (!Number.isNaN(z)) return String(z + 76561197960265728);
  }
  return null;
}

function showLoadingCard(id) {
  const container = document.getElementById('user-container');
  if (!container) return;
  if (document.getElementById('loading-' + id)) return;
  const placeholder = document.createElement('div');
  placeholder.id = 'loading-' + id;
  placeholder.dataset.steamid = id;
  placeholder.className = 'user-card user-box loading';
  placeholder.innerHTML =
    '<div class="user-header"><span class="pill status-pill"><i class="fa-solid fa-arrows-rotate fa-spin"></i></span></div>';
  container.appendChild(placeholder);
}

function applyLoadingState(id) {
  const card = document.getElementById('user-' + id);
  if (card) {
    card.classList.remove('failed', 'success');
    card.classList.add('loading');
    const pill = card.querySelector('.status-pill');
    if (pill) {
      pill.innerHTML = '<i class="fa-solid fa-arrows-rotate fa-spin"></i>';
    }
  } else {
    showLoadingCard(id);
  }
}

function fetchAndInsertSingle(id) {
  const placeholder =
    document.getElementById('loading-' + id) || document.getElementById('user-' + id);
  return fetch('/retry/' + id, { method: 'POST' })
    .then(r => r.text())
    .then(html => {
      const wrapper = document.createElement('div');
      wrapper.innerHTML = html;
      const newCard = wrapper.firstElementChild;
      if (newCard) {
        if (placeholder) {
          placeholder.replaceWith(newCard);
        } else {
          document.getElementById('user-container').appendChild(newCard);
        }
        newCard.classList.add('fade-in');
        setTimeout(() => newCard.classList.add('show'), 10);
      }
      attachHandlers();
      updateRefreshButton();
    })
    .catch(() => {
      const existing = placeholder;
      if (existing) {
        existing.classList.remove('loading');
        existing.classList.add('failed');
        existing.id = 'user-' + id;
      }
      showToast('Failed to load inventory');
      updateRefreshButton();
    });
}

function retryInventory(id) {
  applyLoadingState(id);
  fetchAndInsertSingle(id);
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
  const ids = Array.from(document.querySelectorAll('.user-box.failed')).map(
    el => el.dataset.steamid
  );
  loadUsers(ids).finally(() => {
    btn.disabled = false;
    btn.textContent = original;
  });
}

function loadUsers(ids) {
  if (!ids || !ids.length) return Promise.resolve();
  const promises = [];
  ids.forEach(id => {
    applyLoadingState(id);
    promises.push(fetchAndInsertSingle(id));
  });
  updateRefreshButton();
  return Promise.all(promises).then(() => {
    showResults();
  });
}

function handleScanSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('steamids');
  if (!input) return;
  const raw = input.value || '';
  const ids = extractSteamIds(raw)
    .map(convertToSteam64)
    .filter(Boolean);
  if (!ids.length) {
    showToast('No valid Steam IDs found!');
    return;
  }
  const container = document.getElementById('user-container');
  if (container) container.innerHTML = '';
  updateScanToast(0, ids.length);
  loadUsers(ids).finally(() => hideScanToast());
}

function showResults() {
  const results = document.getElementById('results');
  if (!results) return;
  results.classList.add('fade-in');
  setTimeout(() => {
    results.classList.add('show');
  }, 10);
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
  const form = document.getElementById('scan-form');
  if (form) {
    form.addEventListener('submit', handleScanSubmit);
  }
  if (window.initialIds && window.initialIds.length) {
    loadUsers(window.initialIds);
  }
  attachItemModal();
  if (window.modal && typeof window.modal.initModal === 'function') {
    window.modal.initModal();
  }
  if (document.getElementById('user-container').children.length) {
    showResults();
  }
});
