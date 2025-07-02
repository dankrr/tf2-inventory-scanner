(function (global) {
  let initialized = false;

  function getModal() {
    return document.getElementById('item-modal');
  }

  function getBody() {
    const modal = getModal();
    return modal ? modal.querySelector('.modal-body') : null;
  }

  function openModal(html) {
    const modal = getModal();
    if (!modal) return;
    const body = getBody();
    if (body && html !== undefined) body.innerHTML = html;
    if (typeof modal.showModal === 'function') {
      modal.showModal();
    } else {
      modal.style.display = 'block';
    }
    modal.classList.add('open');
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
    const body = getBody();
    if (body) body.innerHTML = html;
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

  global.modal = { initModal, openModal, closeModal, updateModal };
})(window);
