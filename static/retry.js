function appendCard(html) {
  const wrapper = document.createElement('div');
  wrapper.innerHTML = html;
  const card = wrapper.firstElementChild;
  if (card) {
    document.getElementById('user-container').appendChild(card);
  }
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
  const promises = Array.from(document.querySelectorAll('.retry-pill')).map(el =>
    refreshCard(el.dataset.steamid)
  );
  Promise.all(promises).finally(() => {
    btn.disabled = false;
    btn.textContent = original;
    attachHandlers();
  });
}

function loadUsers(ids) {
  ids.forEach(id => {
    refreshCard(id);
  });
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
});
