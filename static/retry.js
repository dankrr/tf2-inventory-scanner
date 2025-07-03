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

function attachHandlers() {
  document.querySelectorAll('.retry-pill').forEach(el => {
    el.addEventListener('click', () => refreshCard(el.dataset.steamid));
  });
  const btn = document.getElementById('retry-all');
  if (btn) {
    btn.disabled = document.querySelectorAll('.retry-pill').length === 0;
  }

  attachItemModal();
}

function refreshAll() {
  const btn = document.getElementById('retry-all');
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
  const modal = document.getElementById('item-modal');
  if (!modal) return;
  const badgeBox = document.getElementById('modal-badges');

  document.querySelectorAll('.item-card').forEach(card => {
    card.addEventListener('click', () => {
      let data = card.dataset.item;
      if (!data) return;
      try { data = JSON.parse(data); } catch (e) { return; }
      if (window.modal && typeof window.modal.updateHeader === 'function') {
        window.modal.updateHeader(data);
      } else {
        const t = document.getElementById('modal-title');
        const eBox = document.getElementById('modal-effect');
        if (t) t.textContent = data.custom_name || data.name || '';
        if (eBox) eBox.textContent = data.unusual_effect || '';
      }
      if (window.modal && typeof window.modal.generateModalHTML === 'function') {
        const html = window.modal.generateModalHTML(data);
        window.modal.populateModal(html);
      }
      if (window.modal && typeof window.modal.renderBadges === 'function') {
        window.modal.renderBadges(data.badges);
        const spans = badgeBox ? badgeBox.querySelectorAll('span') : [];
        spans.forEach(span => {
          span.addEventListener('click', () => {
            const sec = document.getElementById('modal-spells');
            if (sec) sec.scrollIntoView({ behavior: 'smooth' });
          });
        });
      }
      if (window.modal && typeof window.modal.openModal === 'function') {
        window.modal.openModal();
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  attachHandlers();
  const btn = document.getElementById('retry-all');
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
