/**
 * Apply stored UI preferences for density and quality modes.
 *
 * @returns {void}
 * @example
 * applyStoredPreferences();
 */
function applyStoredPreferences() {
  const compact = localStorage.getItem("compact") === "true";
  const border = localStorage.getItem("borderMode") === "true";
  document.body.classList.toggle("compact", compact);
  document.body.classList.toggle("border-mode", border);
  updateToggleButtons();
}

/**
 * Update global toggle buttons to match current UI modes.
 * Sets `aria-pressed` and dynamic titles for accessibility.
 *
 * @returns {void}
 * @example
 * updateToggleButtons();
 */
function updateToggleButtons() {
  const compactBtn = document.getElementById("toggle-density");
  if (compactBtn) {
    const compactActive = document.body.classList.contains("compact");
    compactBtn.classList.toggle("active", compactActive);
    compactBtn.setAttribute("aria-pressed", String(compactActive));
    compactBtn.title = compactActive
      ? "Disable compact mode"
      : "Enable compact mode";
  }
  const borderBtn = document.getElementById("toggle-quality");
  if (borderBtn) {
    const borderActive = document.body.classList.contains("border-mode");
    borderBtn.classList.toggle("active", borderActive);
    borderBtn.setAttribute("aria-pressed", String(borderActive));
    borderBtn.title = borderActive
      ? "Disable border mode"
      : "Enable border mode";
  }
}

/**
 * Toggle compact density mode for item cards and persist the choice.
 *
 * @returns {void}
 * @example
 * document
 *   .getElementById("toggle-density")
 *   .addEventListener("click", toggleCompactMode);
 */
function toggleCompactMode() {
  const compact = document.body.classList.toggle("compact");
  localStorage.setItem("compact", compact);
  updateToggleButtons();
}

/**
 * Toggle quality border mode for item cards and persist the choice.
 *
 * @returns {void}
 * @example
 * document
 *   .getElementById("toggle-quality")
 *   .addEventListener("click", toggleBorderMode);
 */
function toggleBorderMode() {
  const border = document.body.classList.toggle("border-mode");
  localStorage.setItem("borderMode", border);
  updateToggleButtons();
}

/**
 * Filter a user's inventory items based on search input.
 *
 * @param {Event} event - Input event from the search box.
 * @returns {void}
 * @example
 * searchInput.addEventListener("input", handleUserSearch);
 */
function handleUserSearch(event) {
  const input = event.currentTarget;
  if (!input) return;
  const card = input.closest(".user-card");
  if (!card) return;
  const query = input.value.toLowerCase();
  card.querySelectorAll(".item-wrapper").forEach((wrapper) => {
    const name =
      wrapper.querySelector(".item-name")?.textContent.toLowerCase() || "";
    wrapper.style.display = name.includes(query) ? "" : "none";
  });
}

/**
 * Attach search handlers to all user cards.
 *
 * @returns {void}
 * @example
 * attachUserFeatures();
 */
function attachUserFeatures() {
  document.querySelectorAll(".user-card .user-search").forEach((input) => {
    if (input.dataset.bound) return;
    input.addEventListener("input", handleUserSearch);
    input.dataset.bound = "true";
  });
}

/**
 * Initialize UI features and restore saved preferences.
 *
 * @returns {void}
 * @example
 * document.addEventListener("DOMContentLoaded", initUI);
 */
function initUI() {
  applyStoredPreferences();
  document
    .getElementById("toggle-density")
    ?.addEventListener("click", toggleCompactMode);
  document
    .getElementById("toggle-quality")
    ?.addEventListener("click", toggleBorderMode);
  attachUserFeatures();
}

document.addEventListener("DOMContentLoaded", () => {
  try {
    setupSettingsFab();
  } catch {
    /* ignore */
  }
});
/**
 * Update pressed state in the floating settings menu to match body classes.
 *
 * @returns {void}
 * @example
 * updateSettingsMenuState();
 */
function updateSettingsMenuState() {
  const compactBtn = document.getElementById("settings-compact-btn");
  const borderBtn = document.getElementById("settings-border-btn");
  if (!compactBtn || !borderBtn) return;
  const isCompact = document.body.classList.contains("compact");
  const isBorder = document.body.classList.contains("border-mode");
  compactBtn.setAttribute("aria-pressed", String(isCompact));
  borderBtn.setAttribute("aria-pressed", String(isBorder));
}

/**
 * Hide legacy header display toggles and mark the FAB as active, with a final text-based safety net.
 *
 * @returns {void}
 * @example
 * hideLegacyDisplayToggles();
 */
function hideLegacyDisplayToggles() {
  document.body.classList.add("settings-fab-enabled");
  /**
   * Fully hide an element from view and the accessibility tree.
   *
   * @param {HTMLElement|null} el - Element to hide.
   * @returns {void}
   */
  const hide = (el) => {
    if (el) {
      el.hidden = true;
      el.setAttribute("aria-hidden", "true");
      el.style.display = "none";
    }
  };
  // Only hide by known IDs/classes—do NOT hide by text to avoid catching the new menu.
  hide(document.getElementById("compact-toggle-btn"));
  hide(document.getElementById("border-mode-btn"));
  document
    .querySelectorAll(
      ".toolbar .compact-btn, .toolbar .border-btn, button[data-role='toggle-compact'], button[data-role='toggle-border']",
    )
    .forEach(hide);

  // Final safety net: hide any stray text-labeled header buttons *outside* the settings menu.
  /**
   * Determine whether an element resembles a legacy display toggle outside the settings FAB.
   *
   * @param {Element} el - Candidate element to test.
   * @returns {boolean} True if the element should be hidden.
   */
  const looksLikeLegacy = (el) =>
    !el.closest("#settings-menu") &&
    !el.closest("#settings-fab") &&
    el.id !== "settings-compact-btn" &&
    el.id !== "settings-border-btn";

  const candidates = document.querySelectorAll(
    "button, .btn, [role='button'], a.btn, a[role='button']",
  );
  candidates.forEach((el) => {
    const label = (el.textContent || el.getAttribute("aria-label") || "")
      .trim()
      .toLowerCase();
    if (
      looksLikeLegacy(el) &&
      (label === "compact" || label === "border mode")
    ) {
      hide(el);
    }
  });
}
/**
 * Ensure our floating settings gear, Compact, and Border Mode settings use Font Awesome icons.
 * Safe to call multiple times; only adds icons if missing.
 *
 * @returns {void} No return value.
 * @example
 * setFAIcons();
 */
function setFAIcons() {
  // Gear FAB
  const fab = document.getElementById("settings-fab");
  if (fab && !fab.querySelector("i.fa-solid")) {
    fab.innerHTML = '<i class="fa-solid fa-gear" aria-hidden="true"></i>';
  }
  // Compact icon in the settings menu
  const compactIconWrap = document.querySelector("#settings-compact-btn .icon");
  if (compactIconWrap && !compactIconWrap.querySelector("i.fa-solid")) {
    compactIconWrap.innerHTML =
      '<i class="fa-solid fa-down-left-and-up-right-to-center" aria-hidden="true"></i>';
  }
  // Border Mode icon in the settings menu -> fa-border-none
  let borderIconWrap = document.querySelector(
    "#settings-border-btn .icon, #settings-border .icon",
  );
  if (borderIconWrap && !borderIconWrap.querySelector("i.fa-solid")) {
    borderIconWrap.innerHTML =
      '<i class="fa-solid fa-border-none" aria-hidden="true"></i>';
  } else {
    // Fallback: if no .icon span exists, construct one without breaking the label
    const borderBtn =
      document.getElementById("settings-border-btn") ||
      document.getElementById("settings-border");
    if (borderBtn && !borderBtn.querySelector(".icon")) {
      const labelText =
        borderBtn.querySelector(".label")?.textContent?.trim() ||
        (borderBtn.textContent || "Border Mode").trim();
      borderBtn.innerHTML =
        '<span class="icon" aria-hidden="true"><i class="fa-solid fa-border-none"></i></span>' +
        `<span class="label">${labelText}</span>`;
    }
  }
}

/**
 * Copy legacy header icons into the settings menu so icons stay consistent.
 * Falls back to default emoji if no legacy icons are present.
 *
 * @returns {void}
 * @example
 * syncSettingsIconsFromLegacy();
 */
function syncSettingsIconsFromLegacy() {
  // If we've already set FA icons, don't override them.
  if (document.querySelector("#settings-compact-btn .icon i.fa-solid")) return;
  // Compact
  const compactMenuIcon = document.querySelector("#settings-compact-btn .icon");
  if (compactMenuIcon) {
    let icon = "🗜️"; // default 'clamp' for compact
    const legacy =
      document.querySelector("#compact-toggle-btn .icon") ||
      document.querySelector(".toolbar .compact-btn .icon") ||
      document.querySelector("button[data-role='toggle-compact'] .icon");
    if (legacy && legacy.textContent.trim()) icon = legacy.textContent.trim();
    compactMenuIcon.textContent = icon;
  }
  // Border (optional; keep consistent if you had an icon there)
  const borderMenuIcon = document.querySelector("#settings-border-btn .icon");
  if (borderMenuIcon) {
    let icon = "▦"; // fallback grid-ish icon
    const legacyB =
      document.querySelector("#border-mode-btn .icon") ||
      document.querySelector(".toolbar .border-btn .icon") ||
      document.querySelector("button[data-role='toggle-border'] .icon");
    if (legacyB && legacyB.textContent.trim())
      icon = legacyB.textContent.trim();
    borderMenuIcon.textContent = icon;
  }
}

/**
 * Initialize the floating settings FAB and its dropdown menu.
 *
 * @returns {void}
 * @example
 * setupSettingsFab();
 */
function setupSettingsFab() {
  const fab = document.getElementById("settings-fab");
  const menu = document.getElementById("settings-menu");
  const cBtn = document.getElementById("settings-compact-btn");
  const bBtn = document.getElementById("settings-border-btn");
  if (!fab || !menu) return;
  setFAIcons();
  // Make sure menu icons match whatever you used previously in the header
  syncSettingsIconsFromLegacy();
  hideLegacyDisplayToggles();
  updateSettingsMenuState();

  /**
   * Open the floating settings menu.
   *
   * @returns {void}
   */
  function openMenu() {
    menu.classList.add("open");
    menu.setAttribute("aria-hidden", "false");
    fab.setAttribute("aria-expanded", "true");
    updateSettingsMenuState();
  }
  /**
   * Close the floating settings menu.
   *
   * @returns {void}
   */
  function closeMenu() {
    menu.classList.remove("open");
    menu.setAttribute("aria-hidden", "true");
    fab.setAttribute("aria-expanded", "false");
  }
  if (!fab.dataset.bound) {
    fab.dataset.bound = "1";
    fab.addEventListener("click", (e) => {
      e.stopPropagation();
      if (menu.classList.contains("open")) {
        closeMenu();
      } else {
        openMenu();
      }
    });
    document.addEventListener("click", (e) => {
      if (!menu.contains(e.target) && e.target !== fab) closeMenu();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeMenu();
    });
  }
  if (cBtn && !cBtn.dataset.bound) {
    cBtn.dataset.bound = "1";
    cBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (typeof window.toggleCompactMode === "function") {
        window.toggleCompactMode();
      } else {
        document.body.classList.toggle("compact");
        try {
          localStorage.setItem(
            "compactMode",
            document.body.classList.contains("compact") ? "1" : "0",
          );
        } catch {}
      }
      updateSettingsMenuState();
    });
  }
  if (bBtn && !bBtn.dataset.bound) {
    bBtn.dataset.bound = "1";
    bBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (typeof window.toggleBorderMode === "function") {
        window.toggleBorderMode();
      } else {
        document.body.classList.toggle("border-mode");
        try {
          localStorage.setItem(
            "borderMode",
            document.body.classList.contains("border-mode") ? "1" : "0",
          );
        } catch {}
      }
      updateSettingsMenuState();
    });
  }
  updateSettingsMenuState();
  const origUpdate = window.updateToggleButtons;
  if (typeof origUpdate === "function" && !setupSettingsFab._patched) {
    setupSettingsFab._patched = true;
    window.updateToggleButtons = function () {
      origUpdate.apply(this, arguments);
      updateSettingsMenuState();
    };
  }
}

document.addEventListener("DOMContentLoaded", () => {
  try {
    setupSettingsFab();
  } catch {
    /* ignore */
  }
});
