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

function refreshCard(id) {
  const pill = document.querySelector('#user-' + id + ' .status-pill');
  if (pill) {
    pill.innerHTML = '<i class="fa-solid fa-arrows-rotate fa-spin"></i>';
  }
  return fetch('/retry/' + id, { method: 'POST' })
    .then(r => r.text())
    .then(html => {
      const existing = document.getElementById('user-' + id);
      if (existing) {
        const wrapper = document.createElement('div');
        wrapper.innerHTML = html;
        existing.replaceWith(wrapper.firstElementChild);
      } else {
        appendCard(html);
      }
      attachHandlers();
      showResults();
    });
}

function updateRefreshButton() {
  const btn = document.getElementById('refresh-failed-btn');
  if (!btn) return;
  const hasFailures = document.querySelectorAll('.status-pill.failed').length > 0;
  if (!hasFailures) {
    btn.disabled = true;
    btn.textContent = 'Nothing to Refresh';
    btn.classList.add('btn-disabled');
  } else {
    btn.disabled = false;
    btn.textContent = 'Refresh Failed';
    btn.classList.remove('btn-disabled');
  }
}

function attachHandlers() {
  document.querySelectorAll('.retry-pill').forEach(el => {
    el.addEventListener('click', () => refreshCard(el.dataset.steamid));
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
  const ids = Array.from(document.querySelectorAll('.retry-pill')).map(
    el => el.dataset.steamid
  );
  (async () => {
    for (let i = 0; i < ids.length; i++) {
      updateScanToast(i + 1, ids.length);
      await refreshCard(ids[i]);
    }
    btn.disabled = false;
    btn.textContent = original;
    attachHandlers();
    hideScanToast();
  })();
}

function loadUsers(ids) {
  if (!ids || !ids.length) return;
  (async () => {
    for (let i = 0; i < ids.length; i++) {
      updateScanToast(i + 1, ids.length);
      await refreshCard(ids[i]);
    }
    hideScanToast();
  })();
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
