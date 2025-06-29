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
  const missing = document.getElementById('modal-missing');
  const details = document.getElementById('modal-details');
  const badgeBox = document.getElementById('modal-badges');
  const copyLink = document.getElementById('copy-json');

  const sections = {
    general: document.getElementById('modal-general'),
    killstreak: document.getElementById('modal-killstreak'),
    paint: document.getElementById('modal-paint'),
    spells: document.getElementById('modal-spells'),
    parts: document.getElementById('modal-parts'),
  };
  const sectionWrap = {
    general: document.getElementById('section-general'),
    killstreak: document.getElementById('section-killstreak'),
    paint: document.getElementById('section-paint'),
    spells: document.getElementById('section-spells'),
    parts: document.getElementById('section-parts'),
  };

  function closeModal() {
    modal.style.opacity = '0';
    modal.style.transform = 'scale(0.95)';
    setTimeout(() => modal.close(), 200);
  }

  modal.addEventListener('click', e => {
    if (e.target === modal) closeModal();
  });

  document.querySelectorAll('.item-card').forEach(card => {
    card.addEventListener('click', () => {
      let data = card.dataset.item;
      if (!data) return;
      try {
        data = JSON.parse(data);
      } catch {
        return;
      }
      if (title) title.textContent = data.name || '';
      if (img) {
        if (data.image_url) {
          img.style.display = 'block';
          img.src = data.image_url;
          if (missing) missing.style.display = 'none';
        } else {
          img.style.display = 'none';
          if (missing) missing.style.display = 'flex';
        }
      }

      function setSection(key, entries) {
        const box = sections[key];
        const wrap = sectionWrap[key];
        if (!box || !wrap) return;
        box.innerHTML = '';
        const rows = entries.filter(e => e[1]);
        if (!rows.length) {
          wrap.style.display = 'none';
          return;
        }
        rows.forEach(([label, val]) => {
          const div = document.createElement('div');
          div.textContent = label ? label + ': ' + val : val;
          box.appendChild(div);
        });
        wrap.style.display = '';
      }

      const generalEntries = [];
      if (data.quality) generalEntries.push(['Quality', data.quality]);
      if (data.level) generalEntries.push(['', 'Level ' + data.level]);
      if (data.origin) generalEntries.push(['', data.origin]);
      if (data.unusual_effect) generalEntries.push(['Effect', data.unusual_effect]);
      if (data.is_festivized) generalEntries.push(['Festivized', 'Yes']);
      setSection('general', generalEntries);

      const ksEntries = [];
      if (data.killstreak_tier) ksEntries.push(['Tier', data.killstreak_tier]);
      if (data.sheen) ksEntries.push(['Sheen', data.sheen]);
      if (data.killstreaker) ksEntries.push(['Killstreaker', data.killstreaker]);
      setSection('killstreak', ksEntries);

      if (sections.paint && sectionWrap.paint) {
        sections.paint.innerHTML = '';
        if (data.paint_name) {
          const div = document.createElement('div');
          if (data.paint_hex) {
            const sw = document.createElement('span');
            sw.className = 'paint-swatch';
            sw.style.background = data.paint_hex;
            div.appendChild(sw);
          }
          div.appendChild(document.createTextNode(data.paint_name));
          sections.paint.appendChild(div);
          sectionWrap.paint.style.display = '';
        } else {
          sectionWrap.paint.style.display = 'none';
        }
      }

      if (sections.spells && sectionWrap.spells) {
        sections.spells.innerHTML = '';
        if (Array.isArray(data.spells) && data.spells.length) {
          data.spells.forEach(sp => {
            const li = document.createElement('li');
            li.textContent = sp;
            sections.spells.appendChild(li);
          });
          sectionWrap.spells.style.display = '';
        } else {
          sectionWrap.spells.style.display = 'none';
        }
      }

      if (sections.parts && sectionWrap.parts) {
        sections.parts.innerHTML = '';
        if (Array.isArray(data.strange_parts) && data.strange_parts.length) {
          data.strange_parts.forEach(pt => {
            const li = document.createElement('li');
            li.textContent = pt;
            sections.parts.appendChild(li);
          });
          sectionWrap.parts.style.display = '';
        } else {
          sectionWrap.parts.style.display = 'none';
        }
      }

      if (copyLink) {
        if (window.debugMode) {
          copyLink.style.display = 'inline';
          copyLink.onclick = e => {
            e.preventDefault();
            navigator.clipboard.writeText(JSON.stringify(data, null, 2));
            copyLink.textContent = 'copied!';
            setTimeout(() => (copyLink.textContent = 'copy raw JSON'), 1000);
          };
        } else {
          copyLink.style.display = 'none';
        }
      }

      if (badgeBox) {
        badgeBox.innerHTML = '';
        (data.badges || []).forEach(b => {
          const span = document.createElement('span');
          span.className = 'badge-icon';
          span.textContent = b.icon;
          span.title = b.title;
          let target = '';
          if (b.icon === '🎨') {
            target = b.title.startsWith('Painted') ? 'section-paint' : 'section-spells';
          } else if (b.icon === '⚔️' || b.icon === '💀') {
            target = 'section-killstreak';
          } else if (b.icon === '📊') {
            target = 'section-parts';
          } else if (['👻', '👣', '🎃', '✨'].includes(b.icon)) {
            target = 'section-spells';
          }
          if (target) {
            span.style.cursor = 'pointer';
            span.addEventListener('click', () => {
              const sec = document.getElementById(target);
              if (sec) {
                sec.scrollIntoView({ behavior: 'smooth' });
                sec.classList.add('flash');
                setTimeout(() => sec.classList.remove('flash'), 600);
              }
            });
          }
          badgeBox.appendChild(span);
        });
      }

      if (typeof modal.showModal === 'function') {
        modal.showModal();
      } else {
        modal.style.display = 'block';
      }
      modal.style.opacity = '1';
      modal.style.transform = 'scale(1)';
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
