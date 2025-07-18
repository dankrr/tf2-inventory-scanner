function createPlaceholder(id) {
  const ph = document.createElement('div');
  ph.id = 'user-' + id;
  ph.dataset.steamid = id;
  ph.className = 'user-card user-box loading';
  const spinner = document.createElement('div');
  spinner.className = 'loading-spinner';
  spinner.setAttribute('aria-label', 'Loading');
  ph.appendChild(spinner);
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
      if (window.refreshLazyLoad) {
        window.refreshLazyLoad();
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

function extractSteamIds(text) {
  const tokens = text.trim().split(/\s+/);
  const steam2 = /^STEAM_0:[01]:\d+$/;
  const steam3 = /^\[U:1:\d+\]$/;
  const steam64 = /^\d{17}$/;
  const ids = [];
  const seen = new Set();
  for (const token of tokens) {
    if (!token) continue;
    if (steam2.test(token) || steam3.test(token) || steam64.test(token)) {
      if (!seen.has(token)) {
        seen.add(token);
        ids.push(token);
      }
    }
  }
  return ids;
}

function handleSubmit(e) {
  e.preventDefault();
  const container = document.getElementById('user-container');
  if (!container) return;
  container.innerHTML = '';
  const text = document.getElementById('steamids').value || '';
  const ids = extractSteamIds(text);
  ids.forEach(id => {
    const ph = createPlaceholder(id);
    container.appendChild(ph);
    if (window.io && window.startInventoryFetch) {
      window.startInventoryFetch(id);
    } else {
      fetchUserCard(id);
    }
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
