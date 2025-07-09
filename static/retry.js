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
      }
      attachHandlers();
      updateRefreshButton();
      showResults();
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
  let card = document.getElementById('user-' + id);
  if (card) {
    card.classList.remove('failed', 'success');
    card.classList.add('loading');
    const pill = card.querySelector('.status-pill');
    if (pill) {
      pill.innerHTML = '<i class="fa-solid fa-arrows-rotate fa-spin"></i>';
    }
  } else {
    showLoadingCard(id);
    card = document.getElementById('loading-' + id);
  }
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
    if (
      !document.getElementById('user-' + id) &&
      !document.getElementById('loading-' + id)
    ) {
      showLoadingCard(id);
    }
    promises.push(fetchAndInsertSingle(id));
  });
  return Promise.all(promises);
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
