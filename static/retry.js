// ---- Global Scan Toast controller (shared by submit.js and retry.js) ----
(function () {
  /**
   * Retrieve the scan progress toast element.
   *
   * @returns {HTMLElement|null} Toast node or {@code null} if missing.
   * @example
   * const node = el();
   */
  function el() {
    return document.getElementById("scan-toast");
  }

  let total = 0;
  let current = 0;
  let visible = false;

  /**
   * Render the toast with current progress information.
   *
   * @returns {void}
   * @example
   * render();
   */
  function render() {
    const node = el();
    if (!node) return;
    const label =
      total > 0
        ? `Scanning ${Math.min(current, total)} of ${total} inventories...`
        : "Scanning...";
    // Font Awesome spinner to match Retry pill style
    node.innerHTML =
      '<i class="fa-solid fa-arrows-rotate fa-spin" aria-hidden="true"></i>' +
      '<span class="toast-text">' +
      label +
      "</span>";
    node.classList.remove("hidden");
    visible = true;
  }

  /**
   * Begin a new scan toast cycle.
   *
   * @param {number} t - Total number of scans to run.
   * @returns {void}
   * @example
   * start(5);
   */
  function start(t) {
    total = Number.isFinite(t) && t > 0 ? t : 0;
    current = 0;
    render();
  }

  /**
   * Increment progress and re-render when visible.
   *
   * @returns {void}
   * @example
   * tick();
   */
  function tick() {
    current += 1;
    if (visible) render();
  }

  /**
   * Hide and reset the scan toast.
   *
   * @returns {void}
   * @example
   * finish();
   */
  function finish() {
    const node = el();
    if (!node) return;
    node.classList.add("hidden");
    node.innerHTML = "";
    visible = false;
    total = 0;
    current = 0;
  }

  // Expose globally
  window.scanToast = { start, tick, finish };
})();

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
 * Count completed user cards in the Completed bucket.
 *
 * @returns {number} Total number of completed user cards.
 * @example
 * const completed = getCompletedUsers();
 */
function getCompletedUsers() {
  const completed = document.getElementById("completed-container");
  if (!completed) return 0;
  return completed.querySelectorAll(".user-card").length;
}

/**
 * Hide or show the entire "Completed" bucket when empty or populated.
 *
 * @param {number} completedCount - Number of completed user cards.
 * @returns {void}
 * @example
 * toggleCompletedBucket(5);
 */
function toggleCompletedBucket(completedCount) {
  const completedContainer = document.getElementById("completed-container");
  if (!completedContainer) return;
  let wrapper =
    document.getElementById("completed-bucket") ||
    completedContainer.closest('[data-bucket="completed"]') ||
    completedContainer.closest(".bucket") ||
    completedContainer.parentElement;
  if (wrapper) {
    wrapper.classList.toggle("bucket-hidden", completedCount === 0);
  }
}

/**
 * Toggle visibility for both Failed and Completed buckets based on counts.
 *
 * @returns {void}
 * @example
 * updateBucketVisibility();
 */
function updateBucketVisibility() {
  toggleFailedBucket(getFailedUsers().length);
  toggleCompletedBucket(getCompletedUsers());
}

/**
 * Enable or disable the "Refresh Failed" buttons based on failures.
 * Toggles visibility of the floating refresh control.
 *
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
  // Keep bucket visibility in sync whenever counts can change.
  updateBucketVisibility();
}

document.addEventListener("DOMContentLoaded", () => {
  // Ensure initial visibility is correct on load.
  updateBucketVisibility();
  updateRefreshButton();
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
/**
 * Retry all failed scans in parallel with progress feedback.
 *
 * @returns {Promise<void>} Resolves when all retries complete.
 * @example
 * await refreshAll();
 */
async function refreshAll() {
  const failed = getFailedUsers();
  if (failed.length === 0) {
    updateRefreshButton();
    return;
  }

  updateRefreshButton();
  // Start shared scan toast for the refresh path
  if (window.scanToast) window.scanToast.start(failed.length);

  // Run retries in parallel with progress feedback
  const tasks = failed.map((id) =>
    retryInventory(id)
      .catch(() => {})
      .finally(() => {
        updateRefreshButton();
        if (window.scanToast) window.scanToast.tick();
      }),
  );
  await Promise.allSettled(tasks);

  // Hide toast when everything truly done
  if (window.scanToast) window.scanToast.finish();

  // After everything finished, if 0 failures remain AND there is at least one completed,
  // hide Completed bucket only when all cards are successful.
  const remainingFails = getFailedUsers().length;
  const completedCount = getCompletedUsers();
  if (remainingFails === 0 && completedCount > 0) {
    const totalCards =
      completedCount +
      document.querySelectorAll("#failed-container .user-card.failed").length;
    if (totalCards === completedCount) {
      toggleCompletedBucket(completedCount);
    }
  }
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

  queueMicrotask(() => {
    try {
      const modal = document.querySelector(".item-modal, #item-modal, .modal"); // be generous
      if (!modal) return;
      appendFestivizedToModal(modal, data);
    } catch (err) {
      console.warn("Festivized modal patch failed:", err);
    }
  });
}

/**
 * Append a compact "Festivized" row to the modal details before History when present.
 * Prefers `item.is_festivized` and falls back to attribute defindex 2053.
 *
 * @param {HTMLElement} modalEl - Modal element to append details to.
 * @param {object} item - Item payload containing Festivized info.
 * @returns {void} No return value.
 * @example
 * appendFestivizedToModal(document.querySelector('.modal'), { is_festivized: true });
 */
function appendFestivizedToModal(modalEl, item) {
  const isFest =
    !!item?.is_festivized ||
    (Array.isArray(item?.attributes) &&
      item.attributes.some((a) => Number(a?.defindex) === 2053));

  if (!isFest) return;

  const detailsContainer =
    modalEl.querySelector(
      ".item-details, .modal-details, .item-body, .modal-body, .item-props, dl, .content",
    ) || modalEl;

  if (detailsContainer.querySelector("[data-row='festivized']")) return;

  const dl =
    detailsContainer.closest("dl") || detailsContainer.querySelector("dl");
  if (dl) {
    const dt = document.createElement("dt");
    dt.textContent = "Festivized";
    dt.setAttribute("data-row", "festivized");
    dt.classList.add("festivized-row");
    // Keep History at the very bottom if present
    const historyDt =
      dl.querySelector("dt[data-row='history']") ||
      Array.from(dl.querySelectorAll("dt")).find((el) =>
        /history/i.test(el.textContent || ""),
      );
    if (historyDt) {
      dl.insertBefore(dt, historyDt);
    } else {
      dl.appendChild(dt);
    }
    return;
  }

  const p = document.createElement("p");
  p.setAttribute("data-row", "festivized");
  p.textContent = "Festivized";
  p.classList.add("festivized-row");
  // Keep History last if we can find it
  const historyEl =
    detailsContainer.querySelector("[data-row='history']") ||
    Array.from(detailsContainer.querySelectorAll("a, p, div, span")).find(
      (el) => /history/i.test(el.textContent || ""),
    );
  if (historyEl && historyEl.parentNode === detailsContainer) {
    detailsContainer.insertBefore(p, historyEl);
  } else {
    detailsContainer.appendChild(p);
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
