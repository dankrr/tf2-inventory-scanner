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
  const badgeBox = document.getElementById('modal-badges');

  function closeModal() {
    modal.style.opacity = '0';
    setTimeout(() => modal.close(), 200);
  }

  modal.addEventListener('click', e => {
    if (e.target === modal) closeModal();
  });

  document.querySelectorAll('.item-card').forEach(card => {
    card.addEventListener('click', () => {
      let data = card.dataset.item;
      if (!data) return;
      try { data = JSON.parse(data); } catch (e) { return; }
      if (title) title.textContent = data.name || '';
      if (img) img.src = data.image_url || '';
      if (details) {
        details.innerHTML = '';
        const attrs = document.createElement('div');
        if (data.killstreak_tier) {
          const ks = document.createElement('div');
          ks.textContent = data.killstreak_tier;
          attrs.appendChild(ks);
          if (data.sheen) {
            const sh = document.createElement('div');
            sh.textContent = '\u2022 Sheen: ' + data.sheen;
            attrs.appendChild(sh);
          }
          if (data.killstreak_effect) {
            const ke = document.createElement('div');
            ke.textContent = '\u2022 Effect: ' + data.killstreak_effect;
            attrs.appendChild(ke);
          }
        }

        [
          ['Type', data.item_type_name],
          ['Level', data.level],
          ['Origin', data.origin]
        ].forEach(([label, value]) => {
          if (!value) return;
          const div = document.createElement('div');
          div.textContent = label + ': ' + value;
          attrs.appendChild(div);
        });

        if (data.paint_name) {
          const div = document.createElement('div');
          if (data.paint_hex) {
            const sw = document.createElement('span');
            sw.style.display = 'inline-block';
            sw.style.width = '12px';
            sw.style.height = '12px';
            sw.style.marginRight = '4px';
            sw.style.border = '1px solid #333';
            sw.style.borderRadius = '50%';
            sw.style.background = data.paint_hex;
            div.appendChild(sw);
          }
          div.appendChild(document.createTextNode('Paint: ' + data.paint_name));
          attrs.appendChild(div);
        }

        details.appendChild(attrs);

        if (Array.isArray(data.strange_parts) && data.strange_parts.length) {
          const head = document.createElement('h4');
          head.textContent = 'Strange Parts';
          details.appendChild(head);
          data.strange_parts.forEach(part => {
            const div = document.createElement('div');
            div.textContent = part;
            details.appendChild(div);
          });
        }

        if (Array.isArray(data.spells) && data.spells.length) {
          const head = document.createElement('h4');
          head.textContent = 'Spells';
          head.id = 'modal-spells';
          details.appendChild(head);
          data.spells.forEach(sp => {
            const sdiv = document.createElement('div');
            let icon = '';
            const l = sp.toLowerCase();
            if (l.includes('footsteps')) icon = '👣';
            else if (l.includes('exorcism')) icon = '👻';
            else if (l.includes('pumpkin')) icon = '🎃';
            else if (l.includes('paint')) icon = '🎨';
            if (icon) {
              const span = document.createElement('span');
              span.className = 'badge-icon';
              span.textContent = icon;
              span.style.marginRight = '4px';
              sdiv.appendChild(span);
            }
            sdiv.appendChild(document.createTextNode(sp));
            details.appendChild(sdiv);
          });
        }
      }
      if (badgeBox) {
        badgeBox.innerHTML = '';
        const extra = [];
        if (data.paint_name) extra.push({ icon: '🎨', title: 'Painted' });
        if (data.killstreak_tier)
          extra.push({ icon: '⚔️', title: data.killstreak_tier });
        if (data.killstreaker_effect)
          extra.push({ icon: '💀', title: 'Killstreaker Effect' });
        if (Array.isArray(data.strange_parts) && data.strange_parts.length)
          extra.push({ icon: '📊', title: 'Strange Parts' });
        [...(data.badges || []), ...extra].forEach(b => {
          const span = document.createElement('span');
          span.className = 'badge-icon';
          span.textContent = b.icon;
          span.title = b.title;
          span.addEventListener('click', () => {
            const sec = document.getElementById('modal-spells');
            if (sec) sec.scrollIntoView({ behavior: 'smooth' });
          });
          badgeBox.appendChild(span);
        });
      }
      if (typeof modal.showModal === 'function') {
        modal.showModal();
      } else {
        modal.style.display = 'block';
      }
      modal.style.opacity = '1';
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
