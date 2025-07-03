(function (global) {
  let initialized = false;

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
    setTimeout(() => {
      if (typeof modal.close === 'function') {
        modal.close();
      } else {
        modal.style.display = 'none';
      }
    }, 200);
    const body = getBody();
    if (body) body.innerHTML = '';
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
      const ksParts = [];
      ksParts.push(tierMap[data.killstreak_tier] || data.killstreak_tier);
      if (data.sheen) ksParts.push(esc(data.sheen));
      let ksHtml = 'Killstreak: ' + ksParts.join(', ');
      if (data.killstreak_effect) {
        ksHtml += ', <span class="ks-effect">' + esc(data.killstreak_effect) + '</span>';
      }
      attrs.push('<div>' + ksHtml + '</div>');
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

    if (Array.isArray(data.strange_parts) && data.strange_parts.length) {
      attrs.push('<div>Strange Parts: ' + data.strange_parts.map(esc).join(', ') + '</div>');
    }

    let spells = '';
    if (Array.isArray(data.spells) && data.spells.length) {
      spells += '<h4 id="modal-spells">Spells</h4>';
      spells += data.spells.map(sp => '<div>' + esc(sp) + '</div>').join('');
    }

    const details = attrs.join('') + spells;
    const imgTag = '<img src="' + esc(data.image_url || '') + '" width="64" height="64" alt="">';
    return imgTag + '<div id="modal-details">' + details + '</div>';
  }

  function updateHeader(data) {
    const title = document.getElementById('modal-title');
    const effectBox = document.getElementById('modal-effect');
    if (title) title.textContent = data.custom_name || data.name || '';
    if (effectBox) effectBox.textContent = data.unusual_effect || '';
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
  };
})(window);
