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
if (window.document.querySelector('.modal-body').innerHTML !== '') {
  throw new Error('Modal body should be cleared');
}
modal.renderBadges([{ icon: '🌈', title: 'Weapon color spell' }]);
if (!window.document.querySelector('#modal-badges').textContent.includes('🌈')) {
  throw new Error('Badge not rendered');
}
console.log('Modal tests passed');

