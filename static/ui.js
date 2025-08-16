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
