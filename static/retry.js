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
  const img = document.getElementById('modal-img');
  const details = document.getElementById('modal-details');
  const close = document.getElementById('modal-close');
  if (close) close.addEventListener('click', () => modal.close());

  document.querySelectorAll('.item-card').forEach(card => {
    card.addEventListener('click', () => {
      let data = card.dataset.item;
      if (!data) return;
      try {
        data = JSON.parse(data);
      } catch (e) {
        console.error('Invalid item data', e, data);
        return;
      }
      if (title) title.textContent = data.name || '';
      if (img) img.src = data.image_url || '';
      if (details) {
        details.innerHTML = '';
        if (data.custom_name) {
          const div = document.createElement('div');
          div.innerHTML = '<b>Custom Name:</b> ' + data.custom_name;
          details.appendChild(div);
        }
        if (data.custom_desc) {
          const div = document.createElement('div');
          div.style.whiteSpace = 'pre-line';
          div.textContent = data.custom_desc;
          details.appendChild(div);
        }
        if (data.spells && data.spells.length) {
          const div = document.createElement('div');
          div.innerHTML = '<b>Spells:</b> ' + data.spells.join(', ');
          details.appendChild(div);
        }
        const fields = [
          ['Type', data.item_type_name],
          ['Level', data.level],
          ['Origin', data.origin],
          ['Killstreak', data.killstreak_tier],
          ['Sheen', data.sheen],
          ['Killstreaker', data.killstreaker],
          ['Festivized', data.is_festivized ? 'Yes' : null],
          ['Paint', data.paint_name],
          ['Strange Parts', (data.strange_parts || []).join(', ')],
        ];
        fields.forEach(([label, value]) => {
          if (!value) return;
          const div = document.createElement('div');
          if (label === 'Paint' && data.paint_hex) {
            const sw = document.createElement('span');
            sw.style.display = 'inline-block';
            sw.style.width = '12px';
            sw.style.height = '12px';
            sw.style.marginRight = '4px';
            sw.style.background = data.paint_hex;
            div.appendChild(sw);
          }
          div.appendChild(document.createTextNode(label + ': ' + value));
          details.appendChild(div);
        });
      }
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
