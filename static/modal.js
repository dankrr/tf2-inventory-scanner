(function (global) {
  let initialized = false;
  let closeTimer = null;

  const GRADE_ACCENTS = {
    'civilian grade': '#9ed9ff',
    'freelance grade': '#5d8eff',
    'mercenary grade': '#8c63ff',
    'commando grade': '#e65bff',
    'assassin grade': '#ffa347',
    'elite grade': '#ff5e5e',
  };

  /**
   * Escape user-sourced values before injecting HTML.
   *
   * @param {string|number|null|undefined} str - Raw value to escape.
   * @returns {string} HTML-safe string.
   */
  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

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

  /**
   * Return the CSS class suffix for a grade label.
   *
   * @param {string|null|undefined} gradeName - Grade label from enriched item data.
   * @returns {string} Safe CSS suffix, or an empty string when grade is missing.
   */
  function gradeClassSuffix(gradeName) {
    if (!gradeName) return '';
    return String(gradeName).toLowerCase().replace(/\s+/g, '-');
  }

  /**
   * Return a short display label for TF2 grade chips.
   *
   * @param {string|null|undefined} gradeName - Full grade label.
   * @returns {string} Grade label without trailing "Grade".
   */
  function shortGradeLabel(gradeName) {
    if (!gradeName) return '';
    return String(gradeName).replace(/\s+Grade$/i, '').trim();
  }

  /**
   * Build modal detail rows in a sectioned layout while keeping existing labels for tests/compat.
   *
   * @param {Record<string, any>} data - Item payload from `data-item`.
   * @returns {string} HTML string for modal body content.
   */
  function generateModalHTML(data) {
    if (!data) return '';
    const esc = escapeHtml;

    const coreRows = [];
    const pricingRows = [];

    const tierMap = { 1: 'Killstreak', 2: 'Specialized', 3: 'Professional' };
    const tierName = data.killstreak_tier ? tierMap[data.killstreak_tier] || data.killstreak_tier : null;

    if (data.unusual_effect) {
      const name = typeof data.unusual_effect === 'object'
        ? data.unusual_effect.name
        : data.unusual_effect;
      if (name) coreRows.push('<div><strong>Unusual Effect:</strong> ' + esc(name) + '</div>');
    }

    [
      ['Type', data.item_type_name],
      ['Level', data.level],
      [
        'Craftable',
        typeof data.craftable === 'boolean'
          ? data.craftable
            ? 'Craftable'
            : 'Uncraftable'
          : null,
      ],
      ['Origin', data.origin],
      ['Paintkit', data.paintkit_name],
      ['Crate series', data.crate_series_name],
    ].forEach(([label, value]) => {
      if (!value) return;
      coreRows.push('<div><strong>' + esc(label) + ':</strong> ' + esc(value) + '</div>');
    });

    if (tierName || data.sheen || data.killstreak_effect) {
      let info = '<div class="killstreak-info">';
      if (tierName) info += '<span class="killstreak-tier">' + esc(tierName) + '</span>';
      if (data.sheen) {
        const bgStyle = data.sheen_gradient_css || `background-color:${esc(data.sheen_color || '#ccc')}`;
        info += '<span class="sheen"><span class="sheen-dot" style="' + bgStyle + '"></span>' + esc(data.sheen) + '</span>';
      }
      if (data.killstreak_effect) info += '<span class="killstreaker">| ' + esc(data.killstreak_effect) + '</span>';
      info += '</div>';
      coreRows.push(info);
    }

    if (data.paint_name) {
      let paint = '<div><strong>Paint:</strong> ';
      if (data.paint_hex) {
        paint += '<span class="paint-dot" style="background:' + esc(data.paint_hex) + '"></span>';
      }
      paint += esc(data.paint_name) + '</div>';
      coreRows.push(paint);
    }

    if (data.wear_name) coreRows.push('<div><strong>Wear:</strong> ' + esc(data.wear_name) + '</div>');
    if (data.wear_float !== undefined && data.wear_float !== null) {
      coreRows.push('<div><strong>Wear Float:</strong> ' + esc(Number(data.wear_float).toFixed(4)) + '</div>');
    }

    if (data.custom_description) {
      coreRows.push('<div><strong>Custom Desc:</strong> ' + esc(data.custom_description) + '</div>');
    }

    if (data.formatted_price || data.price_string) {
      pricingRows.push('<div><strong>Price:</strong> ' + esc(data.formatted_price || data.price_string) + '</div>');
    }

    if (data.quantity && Number(data.quantity) > 1) {
      pricingRows.push('<div><strong>Quantity:</strong> ×' + esc(data.quantity) + '</div>');
    }

    let spells = '';
    if (Array.isArray(data.spells) && data.spells.length) {
      spells += '<section class="modal-section"><h4 id="modal-spells">Spells</h4><ul>';
      data.spells.forEach((sp) => {
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
      spells += '</ul></section>';
    }

    let history = '';
    if (data.id && (!data.quantity || data.quantity <= 1) && !data._hidden) {
      const url = 'https://next.backpack.tf/item/' + esc(data.id);
      history = '<section class="modal-section modal-section-history"><div><a href="' + url + '" target="_blank" rel="noopener" class="history-link">History🔎</a>';
      if (data.trade_hold_expires) {
        const dateStr = new Date(data.trade_hold_expires * 1000).toLocaleString();
        history += ' Tradable after: ' + esc(dateStr);
      }
      history += '</div></section>';
    }

    const badgeParts = [];
    if (data.grade_name) {
      const cls = gradeClassSuffix(data.grade_name);
      const gradeLabel = data.grade_short_name || shortGradeLabel(data.grade_name);
      badgeParts.push('<span class="meta-badge grade-badge grade-' + esc(cls) + '" title="' + esc(data.grade_name) + '">' + esc(gradeLabel) + '</span>');
    }
    if (data.wear_name) {
      badgeParts.push('<span class="meta-badge wear-badge">' + esc(data.wear_name) + '</span>');
    }
    if (data.paintkit_name) {
      badgeParts.push('<span class="meta-badge">' + esc(data.paintkit_name) + '</span>');
    }
    if (data.is_uncraftable === true || data.uncraftable === true || data.craftable === false) {
      badgeParts.push('<span class="meta-badge uncraftable-badge">Uncraftable</span>');
    }

    const imgTag = '<div class="modal-media-wrap"><img class="modal-main-image" src="' + esc(data.image_url || '') + '" width="96" height="96" alt=""></div>';
    const badgeRow = badgeParts.length ? '<section class="modal-section modal-section-badges"><div class="modal-chip-row">' + badgeParts.join('') + '</div></section>' : '';
    const core = coreRows.length ? '<section class="modal-section modal-section-core"><h4>Details</h4><div id="modal-details">' + coreRows.join('') + '</div></section>' : '';
    const pricing = pricingRows.length ? '<section class="modal-section modal-section-pricing"><h4>Pricing</h4><div>' + pricingRows.join('') + '</div></section>' : '';

    return '<div class="modal-layout">' + imgTag + '<div class="modal-sections">' + badgeRow + core + pricing + spells + history + '</div></div>';
  }

  /**
   * Update modal header labels and accent color based on item quality/grade.
   *
   * @param {Record<string, any>} data - Item payload from `data-item`.
   * @returns {void}
   */
  function updateHeader(data) {
    const modal = getModal();
    const title = document.getElementById('modal-title');
    const custom = document.getElementById('modal-custom-name');
    const effectBox = document.getElementById('modal-effect');

    if (title) {
      let text = '';
      if (data.killstreak_name) {
        if (["Specialized", "Professional"].includes(data.killstreak_name)) {
          text += data.killstreak_name + ' Killstreak ';
        } else {
          text += data.killstreak_name + ' ';
        }
      }
      text += data.display_name || data.composite_name || data.name || '';
      title.textContent = text.trim();
    }

    if (custom) custom.textContent = data.custom_name || '';

    let effectText = '';
    if (data.unusual_effect) {
      effectText = typeof data.unusual_effect === 'object'
        ? data.unusual_effect.name || ''
        : data.unusual_effect;
    }
    if (effectBox) effectBox.textContent = effectText;

    if (modal) {
      const gradeKey = String(data.grade_name || '').toLowerCase();
      const accent = GRADE_ACCENTS[gradeKey] || data.quality_color || '#7289da';
      modal.style.setProperty('--modal-accent', accent);
    }
  }

  /**
   * Render unique badges in the modal header and skip duplicate symbols.
   *
   * @param {Array<{icon?: string, title?: string}>} badges - Badge list from item payload.
   * @returns {void}
   */
  function renderBadges(badges) {
    const box = document.getElementById('modal-badges');
    if (!box) return;
    box.innerHTML = '';
    const seen = new Set();
    (badges || []).forEach((b) => {
      if (!b || !b.icon) return;
      const key = `${b.icon}|${b.title || ''}`;
      if (seen.has(key)) return;
      seen.add(key);
      const span = document.createElement('span');
      span.className = 'badge';
      span.dataset.icon = b.icon;
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
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });
    document.addEventListener('keydown', (e) => {
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
    updateModal,
  };
})(window);
