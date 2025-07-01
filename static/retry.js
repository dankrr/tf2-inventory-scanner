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
  const effectBox = document.getElementById('modal-effect');
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
      let data = {};
      try {
        data = JSON.parse(card.dataset.item || '{}');
      } catch (e) {
        data = {};
      }

      if (title) title.textContent = data.custom_name || data.name || '';

      if (effectBox) {
        effectBox.textContent = data.unusual_effect || '';
        effectBox.style.display = data.unusual_effect ? 'block' : 'none';
      }

      if (img) img.src = data.image_url || '';

      if (details) {
        details.innerHTML = '';
        if (!data || Object.keys(data).length === 0) {
          const miss = document.createElement('div');
          miss.className = 'missing';
          details.appendChild(miss);
        } else {
          const attrs = document.createElement('div');

          if (data.paintkit || data.wear) {
            const wp = document.createElement('div');
            if (data.paintkit) {
              wp.textContent = 'War Paint: ' + data.paintkit;
              if (data.wear) wp.textContent += ' (' + data.wear + ')';
            } else if (data.wear) {
              wp.textContent = data.wear;
            }
            attrs.appendChild(wp);
          }

          if (data.killstreak_tier || data.sheen || data.killstreaker) {
            const tierMap = {1: 'Killstreak', 2: 'Specialized', 3: 'Professional'};
            const ksParts = [];
            if (data.killstreak_tier) {
              ksParts.push(tierMap[data.killstreak_tier] || data.killstreak_tier);
            }
            if (data.sheen) ksParts.push(data.sheen);
            if (data.killstreaker) ksParts.push(data.killstreaker);
            const ks = document.createElement('div');
            ks.textContent = 'Killstreak: ' + ksParts.join(', ');
            attrs.appendChild(ks);
          }

          if (Array.isArray(data.strange_parts) && data.strange_parts.length) {
            const ul = document.createElement('ul');
            data.strange_parts.forEach(p => {
              const li = document.createElement('li');
              li.textContent = p;
              ul.appendChild(li);
            });
            attrs.appendChild(ul);
          }

          if (Array.isArray(data.spells) && data.spells.length) {
            const head = document.createElement('h4');
            head.textContent = 'Spells';
            attrs.appendChild(head);
            const ul = document.createElement('ul');
            data.spells.forEach(sp => {
              const li = document.createElement('li');
              li.textContent = sp;
              ul.appendChild(li);
            });
            attrs.appendChild(ul);
          }

          details.appendChild(attrs);
        }
      }
      if (badgeBox) {
        badgeBox.innerHTML = '';
        (data.badges || []).forEach(b => {
          const span = document.createElement('span');
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
