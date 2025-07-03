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

