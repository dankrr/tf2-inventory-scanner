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

document.addEventListener("DOMContentLoaded", initUI);

if (window.attachHandlers) {
  const old = window.attachHandlers;
  window.attachHandlers = function () {
    old();
    attachUserFeatures();
  };
} else {
  window.attachHandlers = attachUserFeatures;
}

/**
 * Update pressed state in the floating settings menu to match body classes.
 *
 * @returns {void}
 * @example
 * updateSettingsMenuState();
 */
function updateSettingsMenuState() {
  const compactBtn = document.getElementById("settings-compact");
  const borderBtn = document.getElementById("settings-border");
  if (!compactBtn || !borderBtn) return;
  const isCompact = document.body.classList.contains("compact");
  const isBorder = document.body.classList.contains("border-mode");
  compactBtn.setAttribute("aria-pressed", String(isCompact));
  borderBtn.setAttribute("aria-pressed", String(isBorder));
}

/**
 * Hide legacy header display toggles and mark the FAB as active.
 *
 * @returns {void}
 * @example
 * hideLegacyDisplayToggles();
 */
function hideLegacyDisplayToggles() {
  document.body.classList.add("settings-fab-enabled");
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
  const cBtn = document.getElementById("settings-compact");
  const bBtn = document.getElementById("settings-border");
  if (!fab || !menu) return;

  function openMenu() {
    menu.classList.add("open");
    menu.setAttribute("aria-hidden", "false");
    fab.setAttribute("aria-expanded", "true");
    updateSettingsMenuState();
  }
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
    hideLegacyDisplayToggles();
  } catch {
    /* ignore */
  }
  try {
    setupSettingsFab();
  } catch {
    /* ignore */
  }
});
