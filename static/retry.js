function refreshCard(id) {
  fetch('/retry/' + id, {method: 'POST'})
    .then(r => r.text())
    .then(html => {
      const el = document.getElementById('user-' + id);
      if (el) {
        el.outerHTML = html;
      }
      attachHandlers();
    });
}

function attachHandlers() {
  document.querySelectorAll('.retry-pill').forEach(el => {
    el.addEventListener('click', () => refreshCard(el.dataset.steamid));
  });
  const btn = document.getElementById('retry-all');
  if (btn) {
    btn.disabled = document.querySelectorAll('.retry-pill').length === 0;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  attachHandlers();
  const btn = document.getElementById('retry-all');
  if (btn) {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.retry-pill').forEach(el => refreshCard(el.dataset.steamid));
    });
  }
});
