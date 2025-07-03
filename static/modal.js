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

  function renderBadges(badges) {
    const box = document.getElementById('modal-badges');
    if (!box) return;
    box.innerHTML = '';
    (badges || []).forEach(b => {
      const span = document.createElement('span');
      span.textContent = b.icon;
      span.title = b.title || '';
      box.appendChild(span);
    });
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
  };
})(window);
