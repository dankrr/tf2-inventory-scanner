function createPlaceholder(id) {
  const ph = document.createElement('div');
  ph.id = 'user-' + id;
  ph.dataset.steamid = id;
  ph.className = 'user-card user-box loading';
  return ph;
}

async function fetchUserCard(id) {
  try {
    const resp = await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: [id] })
    });
    if (!resp.ok) throw new Error('Request failed');
    const data = await resp.json();
    const html = Array.isArray(data.html) ? data.html[0] : '';
    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    const card = wrapper.firstElementChild;
    const placeholder = document.getElementById('user-' + id);
    if (card && placeholder) {
      placeholder.replaceWith(card);
      if (window.attachHandlers) {
        window.attachHandlers();
      }
    } else if (placeholder) {
      placeholder.classList.remove('loading');
      placeholder.classList.add('failed');
    }
  } catch (err) {
    console.error('Failed to fetch user', id, err);
    const placeholder = document.getElementById('user-' + id);
    if (placeholder) {
      placeholder.classList.remove('loading');
      placeholder.classList.add('failed');
    }
  }
}

function handleSubmit(e) {
  e.preventDefault();
  const container = document.getElementById('user-container');
  if (!container) return;
  container.innerHTML = '';
  const text = document.getElementById('steamids').value || '';
  const ids = Array.from(new Set(text.split(/\s+/).filter(Boolean)));
  ids.forEach(id => {
    const ph = createPlaceholder(id);
    container.appendChild(ph);
    fetchUserCard(id);
  });
  const results = document.getElementById('results');
  if (results) {
    results.classList.add('show');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form.input-form');
  if (form) {
    form.addEventListener('submit', handleSubmit);
  }
});
