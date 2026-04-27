const { JSDOM } = require('jsdom');
const fs = require('fs');

const modalCode = fs.readFileSync('static/modal.js', 'utf8');

function makeDOM() {
  const dom = new JSDOM(
    '<!DOCTYPE html>' +
    '<dialog id="item-modal">' +
    '  <div class="modal-header">' +
    '    <div id="modal-effect" class="modal-effect"></div>' +
    '    <h3 id="modal-title"></h3>' +
    '    <div id="modal-custom-name"></div>' +
    '    <div id="modal-badges"></div>' +
    '    <button id="modal-close-btn" type="button">✕</button>' +
    '  </div>' +
    '  <div class="modal-body"></div>' +
    '</dialog>',
    { runScripts: 'dangerously' },
  );
  const { window } = dom;
  const script = window.document.createElement('script');
  script.textContent = modalCode;
  window.document.body.appendChild(script);
  return { dom, window };
}

// ── Shared DOM for stateless tests ──────────────────────────────────────────
const { window } = makeDOM();
const modal = window.modal;
modal.initModal();

// ── Basic open/close/populate ────────────────────────────────────────────────
modal.populateModal('<p>Hello</p>');
modal.openModal();
if (!window.document.getElementById('item-modal').classList.contains('open')) {
  throw new Error('Modal should have open class');
}
if (window.document.querySelector('.modal-body').innerHTML.trim() !== '<p>Hello</p>') {
  throw new Error('Modal body not updated');
}

modal.closeModal();
if (window.document.getElementById('item-modal').classList.contains('open')) {
  throw new Error('Modal should be closed');
}

modal.populateModal('<p>Hello</p>');
modal.openModal();
if (!window.document.getElementById('item-modal').classList.contains('open')) {
  throw new Error('Modal should reopen with open class');
}
if (window.document.querySelector('.modal-body').innerHTML.trim() !== '<p>Hello</p>') {
  throw new Error('Modal body not restored after reopen');
}

modal.closeModal();
modal.showItemModal('<p>Hello again</p>');
if (!window.document.getElementById('item-modal').classList.contains('open')) {
  throw new Error('showItemModal should open the modal');
}
if (!window.document.querySelector('.modal-body').innerHTML.includes('Hello again')) {
  throw new Error('showItemModal should populate modal HTML');
}

// ── renderBadges ─────────────────────────────────────────────────────────────
modal.renderBadges([{ icon: '🌈', title: 'Weapon color spell' }]);
if (!window.document.querySelector('#modal-badges').textContent.includes('🌈')) {
  throw new Error('Badge not rendered');
}

// ── Spells ───────────────────────────────────────────────────────────────────
const html1 = modal.generateModalHTML({ spells: ['A Spell', 'B Spell'] });
if (!html1.includes('<li>A Spell</li>') || !html1.includes('<li>B Spell</li>')) {
  throw new Error('String spells not rendered');
}

const html2 = modal.generateModalHTML({
  spells: [
    { name: 'Ghosts', count: 2 },
    { name: 'Fire', count: 1 },
  ],
});
if (!html2.includes('<li>Ghosts (2)</li>')) {
  throw new Error('Spell count not shown');
}
if (!html2.includes('<li>Fire</li>')) {
  throw new Error('Spell object not rendered');
}

// ── Wear / Grade (updated assertions for new label/value row format) ──────────
const htmlWearGrade = modal.generateModalHTML({
  grade_name: 'Elite Grade',
  wear_name: 'Factory New',
  wear_float: 0.042,
});
if (!htmlWearGrade.includes('Elite Grade')) {
  throw new Error('Grade name not rendered');
}
if (!htmlWearGrade.includes('grade-elite-grade')) {
  throw new Error('Grade CSS class not rendered');
}
if (!htmlWearGrade.includes('Factory New')) {
  throw new Error('Wear name not rendered');
}
if (!htmlWearGrade.includes('wear-factory-new')) {
  throw new Error('Wear tier CSS class not rendered');
}
// Wear float now lives in the collapsed debug section
if (!htmlWearGrade.includes('0.0420')) {
  throw new Error('Wear float value not rendered in debug section');
}

// ── History link ──────────────────────────────────────────────────────────────
const htmlHistory = modal.generateModalHTML({ id: 123 });
if (!htmlHistory.includes('https://next.backpack.tf/item/123')) {
  throw new Error('History link missing');
}

const thTs = 1600000000;
const htmlHold = modal.generateModalHTML({ id: 123, trade_hold_expires: thTs });
const expectedDate = new Date(thTs * 1000).toLocaleString();
if (!htmlHold.includes('Tradable after:')) {
  throw new Error('Trade hold text missing');
}
if (!htmlHold.includes(expectedDate)) {
  throw new Error('Trade hold date missing');
}

const htmlStacked = modal.generateModalHTML({ id: 123, quantity: 2 });
if (htmlStacked.includes('backpack.tf')) {
  throw new Error('History link should not show for stacked items');
}

const htmlHidden = modal.generateModalHTML({ id: 123, _hidden: true });
if (htmlHidden.includes('backpack.tf')) {
  throw new Error('History link should not show for hidden items');
}

// ── Killstreak tier labels (new) ──────────────────────────────────────────────
const htmlKs1 = modal.generateModalHTML({ killstreak_tier: 1 });
if (!htmlKs1.includes('❯ Basic Killstreak')) {
  throw new Error('Basic killstreak label not rendered');
}

const htmlKs2 = modal.generateModalHTML({ killstreak_tier: 2 });
if (!htmlKs2.includes('❯❯ Specialized Killstreak')) {
  throw new Error('Specialized killstreak label not rendered');
}

const htmlKs3 = modal.generateModalHTML({ killstreak_tier: 3 });
if (!htmlKs3.includes('❯❯❯ Professional Killstreak')) {
  throw new Error('Professional killstreak label not rendered');
}

// Old raw-number/big killstreak-info block must not appear
if (htmlKs3.includes('class="killstreak-info"')) {
  throw new Error('Old killstreak-info block should not be rendered');
}

// ── Killstreak chip CSS class ─────────────────────────────────────────────────
if (!htmlKs1.includes('ks-tier-1')) throw new Error('ks-tier-1 class missing');
if (!htmlKs2.includes('ks-tier-2')) throw new Error('ks-tier-2 class missing');
if (!htmlKs3.includes('ks-tier-3')) throw new Error('ks-tier-3 class missing');

// ── Price / fallback display (new) ────────────────────────────────────────────
const htmlPrice = modal.generateModalHTML({ price_text: '2.33 ref' });
if (!htmlPrice.includes('2.33 ref')) {
  throw new Error('Price text not rendered');
}
if (htmlPrice.includes('price-badge')) {
  throw new Error('Fallback badge should not appear when price_is_fallback is false');
}

const htmlFallback = modal.generateModalHTML({
  price_text: '2.33 ref',
  price_is_fallback: true,
});
if (!htmlFallback.includes('Base price estimate')) {
  throw new Error('Fallback badge not rendered');
}
if (!htmlFallback.includes('Exact variant not priced')) {
  throw new Error('Fallback explanation note not rendered');
}

const htmlMissingPrice = modal.generateModalHTML({
  price_missing_reason: 'no_price',
});
if (!htmlMissingPrice.includes('No matching price found')) {
  throw new Error('price_missing_reason not converted to human text');
}

const htmlMissingEffect = modal.generateModalHTML({
  price_missing_reason: 'missing_effect_id',
});
if (!htmlMissingEffect.includes('Could not identify unusual effect')) {
  throw new Error('missing_effect_id reason not shown correctly');
}

// ── Tradable / marketable display (new) ───────────────────────────────────────
// Raw tradable:false alone must NOT show Not Tradable
const htmlRawUntradable = modal.generateModalHTML({ tradable: false });
if (htmlRawUntradable.includes('Not Tradable')) {
  throw new Error('Not Tradable should not appear when only tradable:false (no display_not_tradable)');
}

// display_not_tradable:true MUST show Not Tradable
const htmlExplicitUntradable = modal.generateModalHTML({ display_not_tradable: true });
if (!htmlExplicitUntradable.includes('Not Tradable')) {
  throw new Error('Not Tradable should appear when display_not_tradable is true');
}

// ── Unusual effect (new) ──────────────────────────────────────────────────────
const htmlUnusual = modal.generateModalHTML({
  unusual_effect: { name: 'Burning Flames' },
  unusual_effect_id: 13,
});
if (!htmlUnusual.includes('Burning Flames')) {
  throw new Error('Unusual effect name not rendered');
}
// Particle overlay div must be present (baked into generated HTML)
if (!htmlUnusual.includes('modal-effect-bg')) {
  throw new Error('Particle overlay div missing from generated HTML');
}
if (!htmlUnusual.includes('effects/13.png')) {
  throw new Error('Particle effect image not baked into generated HTML');
}

// No particle when no effect
const htmlNoEffect = modal.generateModalHTML({ image_url: '/test.png' });
if (!htmlNoEffect.includes('modal-effect-bg')) {
  throw new Error('modal-effect-bg div should always be present (empty when no effect)');
}

// ── Quality display (new) ─────────────────────────────────────────────────────
const htmlStrange = modal.generateModalHTML({ quality: 'Strange', quality_color: '#cf6a32' });
if (!htmlStrange.includes('Strange')) {
  throw new Error('Quality name not rendered');
}
if (!htmlStrange.includes('#cf6a32')) {
  throw new Error('Quality color not applied');
}

// Normal and Unique quality should be hidden
const htmlNormal = modal.generateModalHTML({ quality: 'Normal' });
if (htmlNormal.includes('quality-chip')) {
  throw new Error('Normal quality chip should not be rendered');
}

// ── Modal image size ──────────────────────────────────────────────────────────
const htmlImg = modal.generateModalHTML({ image_url: '/item.png' });
if (!htmlImg.includes('width="96"') || !htmlImg.includes('height="96"')) {
  throw new Error('Modal image should be 96x96');
}
if (!htmlImg.includes('modal-item-img')) {
  throw new Error('Modal item image class missing');
}

// ── Quick reopen (timer race condition) ───────────────────────────────────────
modal.closeModal();
modal.showItemModal('<p>Race</p>');
setTimeout(() => {
  if (!window.document.getElementById('item-modal').classList.contains('open')) {
    throw new Error('Modal should stay open after quick reopen');
  }
  if (!window.document.querySelector('.modal-body').innerHTML.includes('Race')) {
    throw new Error('Modal body lost content after quick reopen');
  }
  console.log('Modal tests passed');
}, 250);
