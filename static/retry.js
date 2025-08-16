/**
 * Update the progress toast while refreshing failed inventories.
 *
 * @param {number} current - Index of the current scan.
 * @param {number} total - Total number of scans to run.
 * @returns {void}
 */
function updateScanToast(current, total) {
  const toast = document.getElementById("scan-toast");
  if (!toast) return;
  toast.textContent = `\u{1F504} Scanning ${current} of ${total} inventories...`;
  toast.classList.remove("hidden");
  toast.classList.add("show");
}

/**
 * Hide the scan progress toast.
 * @returns {void}
 */
function hideScanToast() {
  const toast = document.getElementById("scan-toast");
  if (!toast) return;
  toast.classList.remove("show");
  setTimeout(() => toast.classList.add("hidden"), 300);
}

/**
 * Retry fetching inventory for a specific user.
 *
 * @param {string} id - Steam ID to refresh.
 * @returns {Promise<void>} Resolves when the card is processed.
 */
async function retryInventory(id) {
  let card = document.getElementById("user-" + id);
  if (card) {
    card.classList.remove("failed", "success");
    card.classList.add("loading");
  }

  const pill = card?.querySelector(".status-pill");
  if (pill) {
    pill.innerHTML = '<i class="fa-solid fa-arrows-rotate fa-spin"></i>';
  }

  try {
    const resp = await fetch("/retry/" + id, { method: "POST" });
    const html = await resp.text();
    const wrapper = document.createElement("div");
    wrapper.innerHTML = html;
    const newCard = wrapper.firstElementChild;
    if (!newCard) return;
    card?.remove();
    const bucket = newCard.classList.contains("failed")
      ? "failed-container"
      : "completed-container";
    if (window.addCardToBucket) {
      window.addCardToBucket(newCard, bucket);
    }
    updateRefreshButton();
    showResults();
  } catch {
    const existing = document.getElementById("user-" + id);
    if (existing) {
      existing.classList.remove("loading");
      existing.classList.add("failed");
    }
    updateRefreshButton();
  }
}

/**
 * Get the list of failed user IDs.
 *
 * @returns {string[]} Array of Steam IDs.
 */
function getFailedUsers() {
  return [
    ...document.querySelectorAll("#failed-container .user-card.failed"),
  ].map((div) => div.dataset.steamid);
}

/**
 * Update the UI count for failed users.
 * @returns {void}
 */
function updateFailedCount() {
  const countEl = document.getElementById("failed-count");
  if (countEl) {
    countEl.textContent = getFailedUsers().length;
  }
}

/**
 * Enable or disable the "Refresh Failed" button based on failures.
 * @returns {void}
 */
function updateRefreshButton() {
  const btn = document.getElementById("refresh-failed-btn");
  if (!btn) return;
  const failures = getFailedUsers().length;
  if (failures === 0) {
    btn.disabled = true;
    btn.textContent = "Nothing to Refresh";
    btn.classList.add("btn-disabled");
  } else {
    btn.disabled = false;
    btn.textContent = `Refresh Failed (${failures})`;
    btn.classList.remove("btn-disabled");
  }
  updateFailedCount();
}

document.addEventListener("DOMContentLoaded", () => {
  updateRefreshButton();
  updateFailedCount();
});

/**
 * Handle retry button clicks for individual cards.
 *
 * @param {MouseEvent} event - Click event.
 * @returns {void}
 */
function handleRetryClick(event) {
  const btn = event.currentTarget;
  if (!btn) return;
  retryInventory(btn.dataset.steamid);
}

/**
 * Attach click handlers and modal logic to current cards.
 * @returns {void}
 */
function attachHandlers() {
  document.querySelectorAll(".retry-button").forEach((btn) => {
    btn.removeEventListener("click", handleRetryClick);
    btn.addEventListener("click", handleRetryClick);
  });
  updateRefreshButton();
  attachItemModal();
  if (window.modal && typeof window.modal.initModal === "function") {
    window.modal.initModal();
  }
  // ensure UI for new/updated cards initializes
  if (window.attachHandlers) {
    /* our ui.js wraps this already */
  }
}

/**
 * Refresh all failed inventories in small batches.
 * @returns {Promise<void>} Resolves when complete.
 */
async function refreshAll() {
  const btn = document.getElementById("refresh-failed-btn");
  if (!btn) return;
  btn.disabled = true;
  const original = btn.textContent;
  btn.textContent = "Refreshing…";
  const ids = getFailedUsers();
  const total = ids.length;
  const BATCH_SIZE = 3;
  let current = 0;
  for (let i = 0; i < ids.length; i += BATCH_SIZE) {
    const batch = ids.slice(i, i + BATCH_SIZE);
    const tasks = batch.map((id) => {
      const card = document.getElementById("user-" + id);
      if (card) card.classList.add("loading");
      updateScanToast(++current, total);
      return retryInventory(id);
    });
    await Promise.all(tasks);
    await new Promise((res) => setTimeout(res, 300));
  }
  btn.disabled = false;
  btn.textContent = original;
  attachHandlers();
  updateRefreshButton();
  updateFailedCount();
  hideScanToast();
}

/**
 * Reveal the results container with a fade-in animation.
 * @returns {void}
 */
function showResults() {
  const results = document.getElementById("results");
  if (!results) return;
  results.classList.add("fade-in");
  setTimeout(() => {
    results.classList.add("show");
  }, 10);
}

/**
 * Handle clicks on item cards to display the modal.
 *
 * @param {MouseEvent|HTMLElement} event - Click event or element.
 * @returns {void}
 */
function handleItemClick(event) {
  const card = event.currentTarget || event;
  let data = card.dataset.item;
  if (!data) return;
  try {
    data = JSON.parse(data);
  } catch {
    return;
  }
  if (window.modal && typeof window.modal.updateHeader === "function") {
    window.modal.updateHeader(data);
  }
  if (
    window.modal &&
    typeof window.modal.setParticleBackground === "function"
  ) {
    window.modal.setParticleBackground(data.unusual_effect_id);
  }
  if (window.modal && typeof window.modal.generateModalHTML === "function") {
    const html = window.modal.generateModalHTML(data);
    if (window.modal.showItemModal) {
      window.modal.showItemModal(html);
    }
  }
  if (window.modal && typeof window.modal.renderBadges === "function") {
    window.modal.renderBadges(data.badges);
  }
}

/**
 * Attach modal click handlers to all item cards.
 * @returns {void}
 */
function attachItemModal() {
  document.querySelectorAll(".item-card").forEach((card) => {
    if (card.dataset.handler) return;
    card.dataset.handler = "true";
    card.addEventListener("click", handleItemClick);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  attachHandlers();
  const btn = document.getElementById("refresh-failed-btn");
  if (btn) {
    btn.addEventListener("click", refreshAll);
  }
  if (window.modal && typeof window.modal.initModal === "function") {
    window.modal.initModal();
  }
  const hasUsers =
    document.getElementById("completed-container").children.length ||
    document.getElementById("failed-container").children.length;
  if (hasUsers) {
    showResults();
  }
});
