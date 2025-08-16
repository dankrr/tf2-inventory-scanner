(function () {
  const LS_KEYS = {
    density: "ui:density", // 'comfortable'|'compact'
    quality: "ui:quality", // 'fill'|'border'
    filter: (sid) => `ui:filter:${sid}`,
    extra: (sid) => `ui:extra:${sid}`,
    search: (sid) => `ui:search:${sid}`,
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
   * Toggle high-value highlighting on a user card.
   *
   * @param {HTMLElement} card - User card element.
   * @param {boolean} on - Whether to enable highlighting.
   * @returns {void}
   * @example
   * applyHighValue(card, true);
   */
  function applyHighValue(card, on) {
    card.classList.toggle("highvalue-on", on);
  }

  /**
   * Filter items in a user card by type, extra filter, and search query.
   *
   * @param {HTMLElement} card - User card element.
   * @param {string} filter - Primary filter name.
   * @param {string} extra - Secondary filter name.
   * @param {string} [query] - Search text.
   * @returns {void}
   * @example
   * filterItems(card, 'unusual', '', 'hat');
   */
  function filterItems(card, filter, extra, query) {
    const items = card.querySelectorAll(".item-wrapper");
    const q = (query || "").trim().toLowerCase();
    applyHighValue(card, extra === "value");
    items.forEach((wrap) => {
      const name = (wrap.dataset.name || "").toLowerCase();
      const keys = Number(wrap.dataset.valueKeys || 0);
      let vis = true;

      switch (filter) {
        case "unusual":
          vis = wrap.dataset.quality === "unusual";
          break;
        case "strange":
          vis = wrap.dataset.quality === "strange";
          break;
        case "cosmetic":
          vis = wrap.dataset.type === "cosmetic";
          break;
        case "weapon":
          vis = wrap.dataset.type === "weapon";
          break;
        default:
          vis = true;
      }

      if (vis) {
        switch (extra) {
          case "dupe":
            vis = wrap.dataset.dupe === "1";
            break;
          case "attrs":
            vis = wrap.dataset.attrs === "1";
            break;
          case "value":
            vis = keys >= 5;
            break;
          default:
            break;
        }
      }

      if (vis && q) vis = name.includes(q);
      wrap.style.display = vis ? "" : "none";
    });
  }

  /**
   * Initialize per-card search and filter behavior.
   *
   * @param {HTMLElement} card - User card element.
   * @returns {void}
   * @example
   * initCardBehavior(document.querySelector('.user-card'));
   */
  function initCardBehavior(card) {
    const steamid =
      card.getAttribute("data-steamid") || card.id.replace("user-", "");
    const itemsWrap = card.querySelector(".items");
    const search = card.querySelector(".inv-search");
    const filterSel = card.querySelector(".filter-select");
    const extraSel = card.querySelector(".extra-select");

    const savedFilter = localStorage.getItem(LS_KEYS.filter(steamid)) || "all";
    const savedExtra = localStorage.getItem(LS_KEYS.extra(steamid)) || "";
    const savedSearch = localStorage.getItem(LS_KEYS.search(steamid)) || "";

    if (search) search.value = savedSearch;
    if (filterSel) filterSel.value = savedFilter;
    if (extraSel) extraSel.value = savedExtra;

    filterItems(card, savedFilter, savedExtra, savedSearch);

    filterSel?.addEventListener("change", () => {
      localStorage.setItem(LS_KEYS.filter(steamid), filterSel.value);
      filterItems(
        card,
        filterSel.value,
        extraSel?.value || "",
        search?.value || "",
      );
    });

    extraSel?.addEventListener("change", () => {
      localStorage.setItem(LS_KEYS.extra(steamid), extraSel.value);
      filterItems(
        card,
        filterSel?.value || "all",
        extraSel.value,
        search?.value || "",
      );
    });

    search?.addEventListener("input", () => {
      localStorage.setItem(LS_KEYS.search(steamid), search.value || "");
      filterItems(
        card,
        filterSel?.value || "all",
        extraSel?.value || "",
        search.value || "",
      );
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
   * @example
   * updateDensityBtn();
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
   * @example
   * updateQualityBtn();
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
   * @example
   * initGlobalToggles();
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
   * @example
   * attachUI();
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

  /**
   * Reapply saved filters and search queries to all user cards.
   * Call after new items append to ensure visibility matches current settings.
   *
   * @returns {void}
   * @example
   * reapplyAllFilters();
   */
  function reapplyAllFilters() {
    document.querySelectorAll(".user-card.user-box").forEach((card) => {
      const steamid =
        card.getAttribute("data-steamid") || card.id.replace("user-", "");
      const filter = localStorage.getItem(LS_KEYS.filter(steamid)) || "all";
      const extra = localStorage.getItem(LS_KEYS.extra(steamid)) || "";
      const search = localStorage.getItem(LS_KEYS.search(steamid)) || "";
      filterItems(card, filter, extra, search);
    });
  }

  // expose public reapply function
  window.reapplyFilters = reapplyAllFilters;

  if (window.attachHandlers) {
    const old = window.attachHandlers;
    window.attachHandlers = function () {
      old();
      attachUI();
      reapplyAllFilters();
    };
  }

  document.addEventListener("DOMContentLoaded", () => {
    initGlobalToggles();
    attachUI();
    reapplyAllFilters();
  });
})();
