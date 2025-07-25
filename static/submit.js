(function () {
function normalizeSteamID(id) {
  const reSteam64 = /^\d{17}$/;
  const reSteam3 = /^\[U:[0-5]:(\d+)\]$/;
  const reSteam2 = /^STEAM_[0-5]:([01]):(\d+)$/;
  const base = 76561197960265728n;

  if (reSteam64.test(id)) return id;

  let m = id.match(reSteam3);
  if (m) {
    const z = BigInt(m[1]);
    return (base + z).toString();
  }

  m = id.match(reSteam2);
  if (m) {
    const y = BigInt(m[1]);
    const z = BigInt(m[2]);
    const accountId = z * 2n + y;
    return (base + accountId).toString();
  }

  if (/^[a-zA-Z0-9_-]+$/.test(id)) {
    return id.trim();
  }

  return null;
}

function createPlaceholder(steamid) {
  const ph = document.createElement('div');
  ph.id = 'user-' + steamid;
  ph.dataset.steamid = steamid;
  ph.className = 'user-card user-box loading';
  ph.innerHTML =
    '<div class="card-header">' +
    steamid +
    '<div class="header-right"></div></div><div class="card-body"><div class="inventory-container"></div></div>';
  const spinner = document.createElement('div');
  spinner.className = 'loading-spinner';
  spinner.setAttribute('aria-label', 'Loading');
  ph.appendChild(spinner);
  const bar = document.createElement('div');
  bar.className = 'user-progress';
  const inner = document.createElement('div');
  inner.className = 'progress-inner';
  inner.id = 'progress-' + steamid;
  bar.appendChild(inner);
  const eta = document.createElement('span');
  eta.className = 'eta-label';
  eta.id = 'eta-' + steamid;
  bar.appendChild(eta);
  ph.appendChild(bar);
  return ph;
}

async function fetchUserCard(id) {
  try {
    const resp = await fetch(`/api/users?_=${Date.now()}`, {
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
  if (e && e.preventDefault) e.preventDefault();
  const container = document.getElementById('user-container');
  if (!container) return;
  // Clear old users to avoid stacking
  container.innerHTML = '';
  const input = document.getElementById('steamids');
  const btn = document.getElementById('check-inventory-btn');
  const text = input.value || '';
  const ids = extractSteamIds(text);
  ids.forEach(id => {
    const steam64 = normalizeSteamID(id);
    if (!steam64) {
      console.error('Invalid SteamID:', id);
      return;
    }
    if (!document.getElementById('user-' + steam64)) {
      const ph = createPlaceholder(steam64);
      container.appendChild(ph);
    }
    if (typeof window.startInventoryFetch === 'function') {
      window.startInventoryFetch(steam64);
    } else {
      console.warn('Socket not connected yet');
      fetchUserCard(steam64);
    }
  });
  const results = document.getElementById('results');
  if (results) {
    results.classList.add('show');
  }
  if (input) input.value = '';
  if (btn) {
    btn.disabled = true;
    setTimeout(() => {
      btn.disabled = false;
    }, 600);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('check-inventory-btn');
  if (!btn) return;
  btn.disabled = true;
  btn.addEventListener('click', e => {
    handleSubmit(e);
  });
});

window.enableSubmitButton = function () {
  const btn = document.getElementById('check-inventory-btn');
  if (btn) btn.disabled = false;
};
})();
