/**
 * Number of unseen results waiting below the viewport.
 * @type {number}
 */
let pendingResults = 0;

/** Button used to jump to newly appended cards. */
const jumpBtn = document.getElementById("jump-btn");

/**
 * Update visibility and text of the jump button.
 * @returns {void}
 */
function updateJumpButton() {
  if (!jumpBtn) return;
  if (pendingResults > 0) {
    jumpBtn.textContent = `New results — Jump ↓ (${pendingResults})`;
    jumpBtn.classList.remove("hidden");
  } else {
    jumpBtn.classList.add("hidden");
  }
}

jumpBtn?.addEventListener("click", () => {
  window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
  pendingResults = 0;
  updateJumpButton();
});

window.addEventListener("scroll", () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 5) {
    pendingResults = 0;
    updateJumpButton();
  }
});

/**
 * Append a user card to the specified bucket.
 * Keeps public cards before private ones in the Completed bucket and
 * auto-scrolls if the bucket bottom is visible; otherwise tracks unseen cards.
 *
 * @param {HTMLElement} card - Rendered user card element.
 * @param {string} containerId - ID of the bucket container.
 * @returns {void} No return value.
 * @example
 * addCardToBucket(cardEl, "completed-container");
 */
function addCardToBucket(card, containerId) {
  const container = document.getElementById(containerId);
  if (!container || !card) return;
  const atBottom =
    container.getBoundingClientRect().bottom <= window.innerHeight + 5;

  // For Completed bucket, keep public first and private last
  if (containerId === "completed-container") {
    const isPrivate = card.classList.contains("private");
    if (isPrivate) {
      // Private cards always go to the very end
      container.appendChild(card);
    } else {
      // Insert before the first private card, if any; otherwise append
      const firstPrivate = container.querySelector(".user-card.private");
      if (firstPrivate) {
        container.insertBefore(card, firstPrivate);
      } else {
        container.appendChild(card);
      }
    }
  } else {
    container.appendChild(card);
  }

  if (window.attachHandlers) {
    window.attachHandlers();
  }
  if (window.refreshLazyLoad) {
    window.refreshLazyLoad();
  }
  if (atBottom) {
    card.scrollIntoView({ behavior: "smooth", block: "end" });
  } else {
    pendingResults += 1;
    updateJumpButton();
  }
}

// Expose for reuse in other modules
window.addCardToBucket = addCardToBucket;

/**
 * Fetch a user card for a given Steam ID and append it to a bucket.
 *
 * @param {string} id - Steam identifier.
 * @returns {Promise<void>} Resolves when the card is processed.
 */
async function fetchUserCard(id) {
  try {
    const resp = await fetch("/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: [id] }),
    });
    if (!resp.ok) throw new Error("Request failed");
    const data = await resp.json();
    const html =
      (Array.isArray(data.completed) && data.completed[0]) ||
      (Array.isArray(data.failed) && data.failed[0]) ||
      "";
    if (!html) return;
    const wrapper = document.createElement("div");
    wrapper.innerHTML = html;
    const card = wrapper.firstElementChild;
    const containerId = card.classList.contains("failed")
      ? "failed-container"
      : "completed-container";
    addCardToBucket(card, containerId);
  } catch (err) {
    console.error("Failed to fetch user", id, err);
  }
}

/**
 * Extract valid Steam IDs from raw text input.
 *
 * @param {string} text - Raw user-provided input.
 * @returns {string[]} Array of unique Steam IDs.
 */
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

/**
 * Handle submission of the scan form.
 * Clears existing results, shows the global scan toast, and
 * concurrently fetches each requested inventory.
 *
 * @param {SubmitEvent} e - Form submission event.
 * @returns {Promise<void>} Resolves when all scans complete.
 * @example
 * form.addEventListener("submit", handleSubmit);
 */
async function handleSubmit(e) {
  e.preventDefault();
  const completed = document.getElementById("completed-container");
  const failed = document.getElementById("failed-container");
  if (completed) completed.innerHTML = "";
  if (failed) failed.innerHTML = "";
  const text = document.getElementById("steamids").value || "";
  const ids = extractSteamIds(text);
  const total = ids.length;
  if (total === 0) return;

  // Start global scan toast for the initial scan batch
  if (window.scanToast) window.scanToast.start(total);
  // Back-compat in case styles rely on .show (handled inside scanToast.render)

  const results = document.getElementById("results");
  if (results) {
    results.classList.add("show");
  }

  await Promise.all(
    ids.map((id) =>
      fetchUserCard(id)
        .catch(() => {})
        .finally(() => {
          if (window.scanToast) window.scanToast.tick();
        }),
    ),
  );

  // Hide toast now that all have settled
  if (window.scanToast) window.scanToast.finish();

  // Hide Completed bucket only if everything succeeded and we actually have completed cards
  const failedCount = document.querySelectorAll(
    "#failed-container .user-card.failed",
  ).length;
  const completedCount = document.querySelectorAll(
    "#completed-container .user-card",
  ).length;
  if (failedCount === 0 && completedCount > 0) {
    const completedContainer = document.getElementById("completed-container");
    if (completedContainer) {
      const wrapper =
        document.getElementById("completed-bucket") ||
        completedContainer.closest('[data-bucket="completed"]') ||
        completedContainer.closest(".bucket") ||
        completedContainer.parentElement;
      if (wrapper) wrapper.classList.add("bucket-hidden");
    }
  }
}

/**
 * Initialize form submission and refresh button bindings after DOM ready.
 *
 * @returns {void}
 * @example
 * document.addEventListener("DOMContentLoaded", initSubmitPage);
 */
function initSubmitPage() {
  const form = document.querySelector("form.input-form");
  if (form) {
    form.addEventListener("submit", handleSubmit);
  }
  // Ensure the Refresh Failed button is wired (safety)
  const btn = document.getElementById("refresh-failed-btn");
  if (btn) {
    btn.removeEventListener("click", refreshAll);
    btn.addEventListener("click", refreshAll);
  }
}

document.addEventListener("DOMContentLoaded", initSubmitPage);
