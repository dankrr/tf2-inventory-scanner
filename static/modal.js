function attachModalHandlers() {
  document.querySelectorAll('.item-card').forEach(card => {
    card.addEventListener('click', () => {
      let item = null;
      try {
        item = JSON.parse(card.dataset.item);
      } catch (err) {
        console.warn('Bad data-item JSON', err, card.dataset.item);
        return;
      }
      const modal = card.closest('.user-card').querySelector('.item-modal');
      if (!modal) return;
      populateModal(modal, item);
      openModal(modal);
    });
  });
  document.querySelectorAll('.item-modal').forEach(modal => {
    const closeBtn = modal.querySelector('.modal-close');
    const bg = modal.querySelector('.modal-bg');
    if (closeBtn) closeBtn.addEventListener('click', () => closeModal(modal));
    if (bg) bg.addEventListener('click', () => closeModal(modal));
  });
}

function openModal(modal) {
  modal.classList.add('open');
}

function closeModal(modal) {
  modal.classList.remove('open');
}

function populateModal(modal, item) {
  const dl = modal.querySelector('.modal-details');
  if (!dl) return;
  dl.innerHTML = '';

  function addRow(label, value) {
    if (value === undefined || value === null || value === '' || (Array.isArray(value) && value.length === 0)) return;
    const dt = document.createElement('dt');
    dt.textContent = label;
    const dd = document.createElement('dd');
    if (typeof value === 'string') {
      dd.innerHTML = value;
    } else {
      dd.textContent = value;
    }
    dl.appendChild(dt);
    dl.appendChild(dd);
  }

  addRow('Custom Name', item.custom_name);
  addRow('Spells', item.spells && item.spells.join(', '));
  addRow('Killstreak Tier', item.killstreak_tier);
  addRow('Sheen', item.sheen);
  addRow('Killstreaker', item.killstreaker);
  if (item.paint_name) {
    const swatch = `<span class="paint-dot" style="background:${item.paint_hex}"></span>`;
    addRow('Paint', `${item.paint_name} ${swatch}`);
  }
  addRow('Strange Parts', item.strange_parts && item.strange_parts.join(', '));
  addRow('Origin', item.origin);
  addRow('Level', item.level);
  addRow('Unusual Effect', item.unusual_effect);
  if (typeof item.is_festivized !== 'undefined') {
    addRow('Festivized', item.is_festivized ? 'Yes' : 'No');
  }
}

if (window.attachHandlers) {
  const oldAttach = window.attachHandlers;
  window.attachHandlers = function () {
    oldAttach();
    attachModalHandlers();
  };
} else {
  window.attachHandlers = attachModalHandlers;
}

document.addEventListener('DOMContentLoaded', attachModalHandlers);
