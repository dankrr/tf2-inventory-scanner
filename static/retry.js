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
  const title = document.getElementById('modal-title');
  const desc = document.getElementById('modal-desc');
  const image = document.getElementById('modal-img');

  modal.addEventListener('click', e => {
    if (e.target === modal) modal.close();
  });

  document.querySelectorAll('.item-card').forEach(card => {
    card.addEventListener('click', () => {
      let data = {};
      try {
        data = JSON.parse(card.dataset.item || '{}');
      } catch (e) {
        data = {};
      }

      if (title)
        title.textContent =
          data.custom_name ||
          (data.unusual_effect ? `${data.unusual_effect} ${data.name}` : data.name);

      if (desc) desc.textContent = data.custom_description || '';

      if (image) {
        image.src = data.image_url || '';
        image.style.display = data.image_url ? 'block' : 'none';
      }

      const modalBody = document.querySelector('#modal-body');
      modalBody.innerHTML = '';

      function addRow(label, value) {
        if (!value) return;
        const row = document.createElement('div');
        row.innerHTML = `<strong>${label}:</strong> ${value}`;
        modalBody.appendChild(row);
      }

      addRow('Unusual Effect', data.unusual_effect);
      addRow(
        'Killstreak Tier',
        {
          1: 'Basic',
          2: 'Specialized',
          3: 'Professional'
        }[data.killstreak_tier]
      );
      addRow('Sheen', data.sheen);
      addRow('Killstreaker', data.killstreaker);
      addRow('Paint', data.paint);
      if (data.paintkit && data.wear) addRow('Skin', `${data.paintkit} (${data.wear})`);
      addRow('Strange Parts', (data.strange_parts || []).join(', '));
      addRow('Crate Series', data.crate_series);

      if (typeof modal.showModal === 'function') {
        modal.showModal();
      } else {
        modal.style.display = 'block';
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
});
