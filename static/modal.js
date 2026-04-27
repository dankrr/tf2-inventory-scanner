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

  function gradeClassSuffix(gradeName) {
    if (!gradeName) return '';
    return String(gradeName).toLowerCase().replace(/\s+/g, '-');
  }

  const KS_TIER_LABELS = {
    1: '❯ Basic Killstreak',
    2: '❯❯ Specialized Killstreak',
    3: '❯❯❯ Professional Killstreak',
  };

  const PRICE_MISSING_REASONS = {
    missing_defindex: 'Could not identify base item.',
    missing_effect_id: 'Could not identify unusual effect.',
    no_price: 'No matching price found.',
    decorated_not_supported: 'Decorated skin pricing not available.',
    variant_not_priced: 'Exact variant not priced.',
  };

  function makeRow(label, valueHtml) {
    const esc = escapeHtml;
    return (
      '<div class="modal-row">' +
      '<span class="modal-label">' + esc(label) + '</span>' +
      '<span class="modal-value">' + valueHtml + '</span>' +
      '</div>'
    );
  }

  function generateModalHTML(data) {
    if (!data) return '';
    const esc = escapeHtml;
    const rows = [];

    // Quality (skip Normal/Unique — not visually interesting)
    if (data.quality && data.quality !== 'Normal' && data.quality !== 'Unique') {
      const qColor = esc(data.quality_color || '#ccc');
      rows.push(makeRow('Quality', '<span class="quality-chip" style="color:' + qColor + '">' + esc(data.quality) + '</span>'));
    }

    // Grade
    if (data.grade_name) {
      const cls = gradeClassSuffix(data.grade_name);
      rows.push(makeRow('Grade', '<span class="meta-badge grade-badge grade-' + esc(cls) + '">' + esc(data.grade_name) + '</span>'));
    }

    // Wear
    if (data.wear_name) {
      const wearSlug = String(data.wear_name).toLowerCase().replace(/\s+/g, '-');
      rows.push(makeRow('Wear', '<span class="wear-tier wear-' + esc(wearSlug) + '">' + esc(data.wear_name) + '</span>'));
    }

    // Craftable — only show when explicitly uncraftable
    if (data.craftable === false) {
      rows.push(makeRow('Craftable', '<span class="attr-chip attr-negative">Uncraftable</span>'));
    }

    // Tradable — only show when backend explicitly flags it
    if (data.display_not_tradable) {
      rows.push(makeRow('Tradable', '<span class="attr-chip attr-negative">Not Tradable</span>'));
    }

    // Killstreak tier
    const ksLabel = data.killstreak_tier ? KS_TIER_LABELS[data.killstreak_tier] || null : null;
    if (ksLabel) {
      rows.push(makeRow('Killstreak', '<span class="ks-chip ks-tier-' + esc(String(data.killstreak_tier)) + '">' + esc(ksLabel) + '</span>'));
    }

    // Sheen
    if (data.sheen) {
      const sStyle = data.sheen_gradient_css || ('background:' + esc(data.sheen_color || '#ccc'));
      rows.push(makeRow('Sheen', '<span class="sheen-dot" style="' + sStyle + '"></span>' + esc(data.sheen)));
    }

    // Killstreaker effect
    if (data.killstreak_effect) {
      rows.push(makeRow('Killstreaker', esc(data.killstreak_effect)));
    }

    // Unusual effect
    if (data.unusual_effect) {
      const name = typeof data.unusual_effect === 'object'
        ? data.unusual_effect.name
        : data.unusual_effect;
      if (name) {
        rows.push(makeRow('Unusual Effect', '<strong class="unusual-chip">' + esc(name) + '</strong>'));
      }
    }

    // Paint
    if (data.paint_name) {
      let paintVal = '';
      if (data.paint_hex) {
        paintVal += '<span class="paint-dot" style="background:' + esc(data.paint_hex) + '"></span>';
      }
      paintVal += esc(data.paint_name);
      rows.push(makeRow('Paint', paintVal));
    }

    // Origin
    if (data.origin) rows.push(makeRow('Origin', esc(data.origin)));

    // Type
    if (data.item_type_name) rows.push(makeRow('Type', esc(data.item_type_name)));

    // Level
    if (data.level != null) rows.push(makeRow('Level', esc(String(data.level))));

    // Crate series
    if (data.crate_series_name) rows.push(makeRow('Crate Series', esc(data.crate_series_name)));

    // Custom description
    if (data.custom_description) rows.push(makeRow('Description', esc(data.custom_description)));

    const detailsHtml = rows.join('');

    // === PRICE SECTION ===
    const priceText = data.price_text || data.formatted_price || data.price_string;
    let priceHtml = '';
    if (priceText || data.price_missing_reason) {
      priceHtml += '<div class="modal-price-section">';
      if (priceText) {
        priceHtml += '<div class="price-display">' + esc(priceText);
        if (data.price_is_fallback) {
          priceHtml += ' <span class="price-badge">Base price estimate</span>';
        }
        priceHtml += '</div>';
      }
      if (data.price_is_fallback && !data.price_missing_reason) {
        priceHtml += '<div class="price-note">Exact variant not priced; showing base item price.</div>';
      }
      if (data.price_missing_reason) {
        const reasonText = PRICE_MISSING_REASONS[data.price_missing_reason] || esc(data.price_missing_reason);
        priceHtml += '<div class="price-note">' + reasonText + '</div>';
      }
      priceHtml += '</div>';
    }

    // === SPELLS SECTION ===
    let spellsHtml = '';
    if (Array.isArray(data.spells) && data.spells.length) {
      spellsHtml += '<h4 id="modal-spells" class="modal-section-title">Spells</h4><ul class="modal-spells-list">';
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
        spellsHtml += '<li>' + line + '</li>';
      });
      spellsHtml += '</ul>';
    }

    // === HISTORY ===
    let historyHtml = '';
    if (data.id && (!data.quantity || data.quantity <= 1) && !data._hidden) {
      const url = 'https://next.backpack.tf/item/' + esc(data.id);
      historyHtml = '<div class="modal-row modal-history">' +
        '<a href="' + url + '" target="_blank" rel="noopener" class="history-link">History🔎</a>';
      if (data.trade_hold_expires) {
        const dateStr = new Date(data.trade_hold_expires * 1000).toLocaleString();
        historyHtml += ' <span class="trade-hold-text">Tradable after: ' + esc(dateStr) + '</span>';
      }
      historyHtml += '</div>';
    }

    // === DEBUG SECTION (collapsed) ===
    const debugEntries = [
      ['defindex', data.defindex],
      ['resolved_defindex', data.resolved_defindex],
      ['sku', data.sku],
      ['price_item_name', data.price_item_name],
      ['price_lookup_key', data.price_lookup_key],
      ['effect_id', data.effect_id != null ? data.effect_id : data.unusual_effect_id],
      ['paintkit', data.paintkit_name],
      ['wear_float', data.wear_float != null ? Number(data.wear_float).toFixed(4) : null],
    ].filter(([, v]) => v != null && v !== '');

    let debugHtml = '';
    if (debugEntries.length) {
      debugHtml = '<details class="modal-debug"><summary>Details</summary>';
      debugEntries.forEach(([k, v]) => {
        debugHtml +=
          '<div class="modal-row debug-row">' +
          '<span class="modal-label">' + esc(k) + '</span>' +
          '<span class="modal-value">' + esc(String(v)) + '</span>' +
          '</div>';
      });
      debugHtml += '</details>';
    }

    // === PARTICLE OVERLAY (baked-in so it persists after body replacement) ===
    let particleHtml = '<div id="modal-effect-bg" class="particle-overlay">';
    if (data.unusual_effect_id) {
      particleHtml += '<img src="/static/images/effects/' + esc(String(data.unusual_effect_id)) + '.png" alt="">';
    }
    particleHtml += '</div>';

    // === IMAGE WRAP ===
    const imgHtml =
      '<div class="modal-img-wrap">' +
      particleHtml +
      '<img src="' + esc(data.image_url || '') + '" width="96" height="96" alt="" class="modal-item-img">' +
      '</div>';

    const innerHtml = detailsHtml + priceHtml + spellsHtml + historyHtml + debugHtml;
    return imgHtml + '<div id="modal-details">' + innerHtml + '</div>';
  }

  function updateHeader(data) {
    const title = document.getElementById('modal-title');
    const custom = document.getElementById('modal-custom-name');
    const effectBox = document.getElementById('modal-effect');

    if (title) {
      let text = '';
      if (data.killstreak_name) {
        if (['Specialized', 'Professional'].includes(data.killstreak_name)) {
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

    const modalEl = document.getElementById('item-modal');
    if (modalEl && data.quality_color) {
      modalEl.style.setProperty('--modal-quality-color', data.quality_color);
    }
  }

  function renderBadges(badges) {
    const box = document.getElementById('modal-badges');
    if (!box) return;
    box.innerHTML = '';
    (badges || []).forEach(b => {
      if (!b || !b.icon) return;
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
    modal.addEventListener('click', e => {
      if (e.target === modal) closeModal();
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') closeModal();
    });
    const closeBtn = document.getElementById('modal-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', closeModal);
    }
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
