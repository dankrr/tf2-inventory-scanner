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
 * Append a user card to the specified bucket.
 * Keeps public cards before private ones in the Completed bucket.
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
      container.appendChild(card);
    } else {
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
  }
}

window.addCardToBucket = addCardToBucket;

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
 * Hide/show the entire "Failed" bucket when it becomes empty/non-empty.
 * Tries several wrappers so this works across layouts.
 *
 * @param {number} failures - Number of failed user cards.
 * @returns {void}
 * @example
 * toggleFailedBucket(0);
 */
function toggleFailedBucket(failures) {
  const failedContainer = document.getElementById("failed-container");
  if (!failedContainer) return;
  // Prefer an explicit wrapper if present, else fall back to a reasonable parent.
  let wrapper =
    document.getElementById("failed-bucket") ||
    failedContainer.closest('[data-bucket="failed"]') ||
    failedContainer.closest(".bucket") ||
    failedContainer.parentElement;
  if (wrapper) {
    wrapper.classList.toggle("bucket-hidden", failures === 0);
  }
}

/**
 * Enable or disable the "Refresh Failed" buttons based on failures.
 * Toggles visibility of the floating refresh control.
 *
 * @param {void} none
 * @returns {void} No return value.
 * @example
 * updateRefreshButton();
 */
function updateRefreshButton() {
  const btn = document.getElementById("refresh-failed-btn");
  const floatBtn = document.getElementById("refresh-floating-btn");
  if (!btn) return;
  const failures = getFailedUsers().length;
  if (failures === 0) {
    btn.disabled = true;
    btn.textContent = "Nothing to Refresh";
    btn.classList.add("btn-disabled");
    if (floatBtn) {
      floatBtn.style.display = "none";
      floatBtn.setAttribute("disabled", "true");
    }
  } else {
    btn.disabled = false;
    btn.textContent = `Refresh Failed (${failures})`;
    btn.classList.remove("btn-disabled");
    if (floatBtn) {
      floatBtn.style.display = "block";
      floatBtn.removeAttribute("disabled");
    }
  }
  updateFailedCount();
  toggleFailedBucket(failures);
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

/** Bind floating buttons (idempotent).
 *
 * @param {void} none
 * @returns {void} No return value.
 * @example
 * setupFloatingControls();
 */
function setupFloatingControls() {
  const topBtn = document.getElementById("scroll-top-btn");
  const refBtn = document.getElementById("refresh-floating-btn");
  const mainRefresh = document.getElementById("refresh-failed-btn");

  if (topBtn && !topBtn.dataset.bound) {
    topBtn.dataset.bound = "1";
    topBtn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  if (refBtn && !refBtn.dataset.bound) {
    refBtn.dataset.bound = "1";
    refBtn.addEventListener("click", () => {
      if (typeof refreshAll === "function") {
        refreshAll();
      } else {
        mainRefresh?.click();
      }
    });
  }
}

/**
 * Attach click handlers, modal logic, and search bindings to current cards.
 *
 * @param {void} none
 * @returns {void} No return value.
 * @example
 * attachHandlers();
 */
function attachHandlers() {
  document.querySelectorAll(".retry-button").forEach((btn) => {
    btn.removeEventListener("click", handleRetryClick);
    btn.addEventListener("click", handleRetryClick);
  });
  updateRefreshButton();
  attachItemModal();
  attachUserSearch();
}

/**
 * Per-user inventory search that filters item wrappers under each user card.
/**
 * Per-user inventory search that filters item wrappers under each user card.
 * Falls back to parsing `.item-card[data-item]` when `data-name` is unavailable.
 *
 * @param {void} none
 * @returns {void} Adjusts item visibility based on the search query.
 * @example
 * attachUserSearch();
 */
function attachUserSearch() {
  document.querySelectorAll(".user-search").forEach((input) => {
    if (input.dataset.bound === "1") return;
    input.dataset.bound = "1";

    const userCard = input.closest(".user-card");
    if (!userCard) return;

    // Support both old and new templates
    const itemsEl =
      userCard.querySelector(".inventory-container") ||
      userCard.querySelector(".items") ||
      userCard.querySelector(".inventory-grid");
    if (!itemsEl) return;

    const wrappers = () => itemsEl.querySelectorAll(".item-wrapper");

    const getName = (wrap) => {
      // Cache once per wrapper
      if (!wrap.dataset.searchName) {
        let nm = (wrap.dataset.name || "").trim();
        if (!nm) {
          const card = wrap.querySelector(".item-card");
          if (card) {
            try {
              const raw =
                card.getAttribute("data-item") || card.dataset.item || "";
              if (raw && raw[0] === "{") {
                const obj = JSON.parse(raw);
                nm =
                  obj.display_name ||
                  obj.composite_name ||
                  obj.base_name ||
                  obj.name ||
                  "";
              }
            } catch {
              /* ignore parse errors */
            }
          }
        }
        wrap.dataset.searchName = (nm || "").toLowerCase();
      }
      return wrap.dataset.searchName;
    };

    const apply = () => {
      const q = (input.value || "").trim().toLowerCase();
      wrappers().forEach((w) => {
        if (!q) {
          w.style.display = "";
          return;
        }
        w.style.display = getName(w).includes(q) ? "" : "none";
      });
    };

    input.addEventListener("input", apply);
    input.addEventListener("search", apply); // supports clear (x)
    apply();
  });
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
  let data = card.getAttribute("data-item") || card.dataset.item || "";
  if (!data || data[0] !== "{") {
    console.warn("Bad data-item on card:", card, data);
    return;
  }
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
 * Remove particle effect images when they fail to load.
 *
 * @returns {void}
 */
function attachEffectFallback() {
  document.querySelectorAll("img.particle-bg").forEach((img) => {
    if (img.dataset.effectFallback) return;
    img.dataset.effectFallback = "true";
    img.addEventListener("error", () => img.remove());
  });
}

/**
 * Delegate modal click handling from inventory buckets so all item cards trigger the modal.
 *
 * @returns {void}
 * @example
 * attachItemModal();
 */
function attachItemModal() {
  // Delegate from stable parents so newly appended cards work too
  const roots = [
    document.getElementById("completed-container"),
    document.getElementById("failed-container"),
    document.getElementById("user-container"),
  ].filter(Boolean);

  roots.forEach((root) => {
    if (root.dataset.modalDelegated === "1") return;
    root.dataset.modalDelegated = "1";
    // Capture phase so overlays/badges can't swallow the click
    root.addEventListener(
      "click",
      (e) => {
        const card = e.target.closest(".item-card");
        if (!card || !root.contains(card)) return;
        handleItemClick({ currentTarget: card });
      },
      true,
    );
  });
  attachEffectFallback();
}

// Initialize effect fallback for existing items
attachEffectFallback();

/**
 * Focus and select the Steam IDs textarea so it's ready for paste.
 * Safe to call multiple times.
 * @returns {void}
 * @example
 * focusSteamInput();
 */
function focusSteamInput() {
  const el =
    document.getElementById("steamids") ||
    document.querySelector('textarea[name="steamids"]');
  if (!el) return;
  // Defer to allow layout/other handlers to settle
  requestAnimationFrame(() => {
    try {
      el.focus();
      el.select(); // highlight all for quick paste
    } catch {}
  });
}

document.addEventListener("DOMContentLoaded", () => {
  // Make input paste-ready immediately
  focusSteamInput();
  attachHandlers();
  const btn = document.getElementById("refresh-failed-btn");
  if (btn) {
    btn.addEventListener("click", refreshAll);
  }
  setupFloatingControls();
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
