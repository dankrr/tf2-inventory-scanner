(function (global) {
  let initialized = false;
  let closeTimer = null;

  function getModal() {
    return document.getElementById('item-modal');
  }

  function getBody() {
    const modal = getModal();
    return modal ? modal.querySelector('.modal-body') : null;
  }

  function openModal() {
    const modal = getModal();
    if (!modal) return;
    if (closeTimer) {
      clearTimeout(closeTimer);
      closeTimer = null;
    }
    if (typeof modal.showModal === 'function') {
      modal.showModal();
    } else {
      modal.style.display = 'block';
    }
    modal.classList.add('open');
  }

  function populateModal(html) {
    const body = getBody();
    if (body) body.innerHTML = html;
  }

  function closeModal() {
    const modal = getModal();
    if (!modal) return;
    modal.classList.remove('open');
    closeTimer = setTimeout(() => {
      if (typeof modal.close === 'function') {
        modal.close();
      } else {
        modal.style.display = 'none';
      }
      const body = getBody();
      if (body) body.innerHTML = '';
      closeTimer = null;
    }, 200);
  }

  function updateModal(html) {
    populateModal(html);
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function generateModalHTML(data) {
    if (!data) return '';
    const esc = escapeHtml;
    const attrs = [];

    if (data.killstreak_tier) {
      const tierMap = { 1: 'Killstreak', 2: 'Specialized', 3: 'Professional' };
      const tierName = tierMap[data.killstreak_tier] || data.killstreak_tier;
      const color = data.sheen_color || '#f97316';
      let ksHtml =
        '<div><span class="badge ks-tier" style="background:' +
        esc(color) + ';">' +
        esc(tierName) +
        '</span>';
      if (data.sheen) {
        ksHtml += ' ' + esc(data.sheen);
      }
      if (data.killstreak_effect) {
        ksHtml += ', <span class="ks-effect">' + esc(data.killstreak_effect) + '</span>';
      }
      ksHtml += '</div>';
      attrs.push(ksHtml);
    }

    if (data.unusual_effect) {
      const name = typeof data.unusual_effect === 'object'
        ? data.unusual_effect.name
        : data.unusual_effect;
      if (name) {
        attrs.push('<div><strong>Unusual Effect:</strong> ' + esc(name) + '</div>');
      }
    }

    ;[
      ['Type', data.item_type_name],
      ['Level', data.level],
      ['Origin', data.origin],
    ].forEach(([label, value]) => {
      if (!value) return;
      attrs.push('<div>' + esc(label) + ': ' + esc(value) + '</div>');
    });

    if (data.paint_name) {
      let html = '<div>';
      if (data.paint_hex) {
        html += '<span class="paint-dot" style="background:' + esc(data.paint_hex) + '"></span>';
      }
      html += 'Paint: ' + esc(data.paint_name) + '</div>';
      attrs.push(html);
    }

    if (data.wear_name) attrs.push('<div>Wear: ' + esc(data.wear_name) + '</div>');

    if (data.paintkit_name) attrs.push('<div>Paintkit: ' + esc(data.paintkit_name) + '</div>');

    if (data.crate_series_name) attrs.push('<div>Crate series: ' + esc(data.crate_series_name) + '</div>');

    if (data.custom_description) attrs.push('<div>Custom Desc: ' + esc(data.custom_description) + '</div>');


    let spells = '';
    if (Array.isArray(data.spells) && data.spells.length) {
      spells += '<h4 id="modal-spells">Spells</h4><ul>';
      data.spells.forEach(sp => {
        let name = '';
        let count = null;
        if (typeof sp === 'string') {
          name = sp;
        } else if (sp && typeof sp === 'object') {
          name = sp.name || '';
          count = sp.count;
        } else {
          name = String(sp || '');
        }
        let line = esc(name);
        if (count && count > 1) {
          line += ' (' + esc(count) + ')';
        }
        spells += '<li>' + line + '</li>';
      });
      spells += '</ul>';
    }

    const details = attrs.join('') + spells;
    const imgTag = '<img src="' + esc(data.image_url || '') + '" width="64" height="64" alt="">';
    return imgTag + '<div id="modal-details">' + details + '</div>';
  }

  function updateHeader(data) {
    const title = document.getElementById('modal-title');
    const custom = document.getElementById('modal-custom-name');
    const effectBox = document.getElementById('modal-effect');
    if (title) title.textContent = data.composite_name || data.name || '';
    if (custom) custom.textContent = data.custom_name || '';
    let effectText = '';
    if (data.unusual_effect) {
      effectText = typeof data.unusual_effect === 'object'
        ? data.unusual_effect.name || ''
        : data.unusual_effect;
    }
    if (effectBox) effectBox.textContent = effectText;
  }

  function renderBadges(badges) {
    const box = document.getElementById('modal-badges');
    if (!box) return;
    box.innerHTML = '';
    (badges || []).forEach(b => {
      const span = document.createElement('span');
      span.textContent = b.icon;
      span.title = b.title || '';
      span.addEventListener('click', () => {
        const sec = document.getElementById('modal-spells');
        if (sec) sec.scrollIntoView({ behavior: 'smooth' });
      });
      box.appendChild(span);
    });
  }

  function setParticleBackground(effectId) {
    const box = document.getElementById('modal-effect-bg');
    if (!box) return;
    if (effectId) {
      const url = '/static/images/effects/' + effectId + '.png';
      box.innerHTML = '<img src="' + url + '" alt="">';
    } else {
      box.innerHTML = '';
    }
  }

  function showItemModal(html) {
    if (!html) {
      console.warn('Empty modal HTML!');
      return;
    }
    populateModal(html);
    openModal();
  }

  function initModal() {
    if (initialized) return;
    const modal = getModal();
    if (!modal) return;
    modal.addEventListener('click', e => {
      if (e.target === modal) closeModal();
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') closeModal();
    });
    initialized = true;
  }

  global.modal = {
    initModal,
    openModal,
    closeModal,
    populateModal,
    renderBadges,
    showItemModal,
    generateModalHTML,
    updateHeader,
    setParticleBackground,
  };
})(window);
