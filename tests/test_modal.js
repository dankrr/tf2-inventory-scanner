const { JSDOM } = require('jsdom');
const fs = require('fs');

const modalCode = fs.readFileSync('static/modal.js', 'utf8');

const dom = new JSDOM('<!DOCTYPE html><dialog id="item-modal"><div id="modal-badges"></div><div class="modal-body"></div></dialog>', { runScripts: 'dangerously' });

const { window } = dom;
window.document.body.appendChild(window.document.getElementById('item-modal'));
const script = window.document.createElement('script');
script.textContent = modalCode;
window.document.body.appendChild(script);

const modal = window.modal;
modal.initModal();
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
modal.renderBadges([{ icon: '🌈', title: 'Weapon color spell' }]);
if (!window.document.querySelector('#modal-badges').textContent.includes('🌈')) {
  throw new Error('Badge not rendered');
}
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

