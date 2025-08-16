(function () {
  const LS_KEYS = {
    density: "ui:density", // 'comfortable'|'compact'
    quality: "ui:quality", // 'fill'|'border'
    filter: (sid) => `ui:filter:${sid}`,
    search: (sid) => `ui:search:${sid}`,
    sort: (sid) => `ui:sort:${sid}`,
  };

  /**
   * Apply density mode to a user card.
   *
   * @param {HTMLElement} card - User card element.
   * @param {'comfortable'|'compact'} mode - Density mode.
   * @returns {void}
   * @example
   * applyDensity(card, 'compact');
   */
  function applyDensity(card, mode) {
    card.classList.toggle("density-compact", mode === "compact");
  }

  /**
   * Apply quality color mode to a user card.
   *
   * @param {HTMLElement} card - User card element.
   * @param {'fill'|'border'} mode - Quality mode.
   * @returns {void}
   * @example
   * applyQuality(card, 'border');
   */
  function applyQuality(card, mode) {
    card.classList.toggle("quality-border", mode === "border");
  }

  /**
   * Filter items in a user card by type and search query.
   *
   * @param {HTMLElement} card - User card element.
   * @param {string} filter - Active filter name.
   * @param {string} [query] - Search text.
   * @returns {void}
   * @example
   * filterItems(card, 'unusual', 'hat');
   */
  function filterItems(card, filter, query) {
    const items = card.querySelectorAll(".item-wrapper");
    const q = (query || "").trim().toLowerCase();
    items.forEach((wrap) => {
      const name = (wrap.dataset.name || "").toLowerCase();
      const keys = Number(wrap.dataset.valueKeys || 0);
      let vis = true;

      switch (filter) {
        case "unusual":
          vis = wrap.classList.contains("quality-unusual");
          break;
        case "strange":
          vis = wrap.classList.contains("quality-strange");
          break;
        case "cosmetic":
          vis = wrap.classList.contains("is-cosmetic");
          break;
        case "weapon":
          vis = wrap.classList.contains("is-weapon");
          break;
        case "dupe":
          vis = wrap.classList.contains("is-duplicate");
          break;
        case "attrs":
          vis = wrap.classList.contains("has-attrs");
          break;
        case "value":
          vis = keys >= 5;
          break;
        default:
          vis = true;
      }
      if (vis && q) vis = name.includes(q);
      wrap.style.display = vis ? "" : "none";
    });
  }

  /**
   * Sort items within a user card.
   *
   * @param {HTMLElement} card - User card element.
   * @param {"name"|"value"} key - Sort key.
   * @returns {void}
   * @example
   * sortItems(card, "value");
   */
  function sortItems(card, key) {
    const container = card.querySelector(".items");
    if (!container) return;
    const items = Array.from(container.querySelectorAll(".item-wrapper"));
    const compare =
      key === "name"
        ? (a, b) =>
            (a.dataset.name || "").localeCompare(
              b.dataset.name || "",
              undefined,
              {
                sensitivity: "base",
              },
            )
        : (a, b) =>
            Number(b.dataset.valueKeys || 0) - Number(a.dataset.valueKeys || 0);
    items.sort(compare);
    let i = 0;
    function batch() {
      const slice = items.slice(i, i + 50);
      slice.forEach((el) => container.appendChild(el));
      i += slice.length;
      if (i < items.length) requestAnimationFrame(batch);
    }
    requestAnimationFrame(batch);
  }

  /**
   * Initialize per-card search and filter behavior.
   *
   * @param {HTMLElement} card - User card element.
   * @returns {void}
   */
  function initCardBehavior(card) {
    const steamid =
      card.getAttribute("data-steamid") || card.id.replace("user-", "");
    const itemsWrap = card.querySelector(".items");
    const search = card.querySelector(".inv-search");
    const chips = card.querySelectorAll(".filters .chip");
    const sortSel = card.querySelector(".sort-select");

    const savedFilter = localStorage.getItem(LS_KEYS.filter(steamid)) || "all";
    const savedSearch = localStorage.getItem(LS_KEYS.search(steamid)) || "";
    const savedSort = localStorage.getItem(LS_KEYS.sort(steamid)) || "default";

    if (search) search.value = savedSearch;

    if (chips.length) {
      chips.forEach((c) =>
        c.classList.toggle("is-active", c.dataset.filter === savedFilter),
      );
      filterItems(card, savedFilter, savedSearch);
    }

    if (sortSel) {
      sortSel.value = savedSort;
      if (savedSort !== "default") sortItems(card, savedSort);
    }

    chips.forEach((chip) => {
      chip.addEventListener("click", () => {
        chips.forEach((c) => c.classList.remove("is-active"));
        chip.classList.add("is-active");
        localStorage.setItem(LS_KEYS.filter(steamid), chip.dataset.filter);
        filterItems(card, chip.dataset.filter, search?.value || "");
      });
    });

    search?.addEventListener("input", () => {
      localStorage.setItem(LS_KEYS.search(steamid), search.value || "");
      const active =
        card.querySelector(".filters .chip.is-active")?.dataset.filter || "all";
      filterItems(card, active, search.value || "");
    });

    sortSel?.addEventListener("change", () => {
      const val = sortSel.value;
      localStorage.setItem(LS_KEYS.sort(steamid), val);
      if (val === "default") return;
      sortItems(card, val);
    });

    if (itemsWrap) {
      itemsWrap.addEventListener(
        "wheel",
        (e) => {
          if (e.shiftKey) {
            itemsWrap.scrollLeft += e.deltaY;
            e.preventDefault();
          }
        },
        { passive: false },
      );
    }
  }

  let densityMode = localStorage.getItem(LS_KEYS.density) || "comfortable";
  let qualityMode = localStorage.getItem(LS_KEYS.quality) || "fill";
  const densityBtn = document.getElementById("density-toggle");
  const qualityBtn = document.getElementById("quality-toggle");

  /**
   * Apply density mode to all user cards.
   *
   * @param {'comfortable'|'compact'} mode - Density mode.
   * @returns {void}
   * @example
   * applyDensityAll('compact');
   */
  function applyDensityAll(mode) {
    document
      .querySelectorAll(".user-card.user-box")
      .forEach((card) => applyDensity(card, mode));
  }

  /**
   * Apply quality mode to all user cards.
   *
   * @param {'fill'|'border'} mode - Quality mode.
   * @returns {void}
   * @example
   * applyQualityAll('border');
   */
  function applyQualityAll(mode) {
    document
      .querySelectorAll(".user-card.user-box")
      .forEach((card) => applyQuality(card, mode));
  }

  /**
   * Update density button label and state.
   *
   * @returns {void}
   */
  function updateDensityBtn() {
    if (!densityBtn) return;
    densityBtn.textContent =
      densityMode === "compact" ? "Comfortable" : "Compact";
    densityBtn.setAttribute("aria-pressed", String(densityMode === "compact"));
  }

  /**
   * Update quality button label and state.
   *
   * @returns {void}
   */
  function updateQualityBtn() {
    if (!qualityBtn) return;
    qualityBtn.textContent = qualityMode === "border" ? "Fill" : "Border";
    qualityBtn.setAttribute("aria-pressed", String(qualityMode === "border"));
  }

  /**
   * Initialize global toggle buttons and apply modes.
   *
   * @returns {void}
   */
  function initGlobalToggles() {
    applyDensityAll(densityMode);
    applyQualityAll(qualityMode);
    updateDensityBtn();
    updateQualityBtn();

    densityBtn?.addEventListener("click", () => {
      densityMode = densityMode === "compact" ? "comfortable" : "compact";
      localStorage.setItem(LS_KEYS.density, densityMode);
      applyDensityAll(densityMode);
      updateDensityBtn();
    });

    qualityBtn?.addEventListener("click", () => {
      qualityMode = qualityMode === "border" ? "fill" : "border";
      localStorage.setItem(LS_KEYS.quality, qualityMode);
      applyQualityAll(qualityMode);
      updateQualityBtn();
    });
  }

  /**
   * Attach UI behavior to new user cards.
   *
   * @returns {void}
   */
  function attachUI() {
    document.querySelectorAll(".user-card.user-box").forEach((card) => {
      if (card.dataset.uiInit === "1") return;
      card.dataset.uiInit = "1";
      applyDensity(card, densityMode);
      applyQuality(card, qualityMode);
      initCardBehavior(card);
    });
  }

  if (window.attachHandlers) {
    const old = window.attachHandlers;
    window.attachHandlers = function () {
      old();
      attachUI();
    };
  }

  document.addEventListener("DOMContentLoaded", () => {
    initGlobalToggles();
    attachUI();
  });
})();
