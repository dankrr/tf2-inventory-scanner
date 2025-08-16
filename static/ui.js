(function () {
  const LS_KEYS = {
    density: (sid) => `ui:density:${sid}`, // 'comfortable'|'compact'
    quality: (sid) => `ui:quality:${sid}`, // 'fill'|'border'
    hv: (sid) => `ui:highvalue:${sid}`, // 'on'|'off'
    filter: (sid) => `ui:filter:${sid}`, // 'all'|'unusual'|...
    search: (sid) => `ui:search:${sid}`, // last query
  };

  /**
   * Apply density mode to a user card.
   *
   * @param {HTMLElement} card - User card element.
   * @param {string} mode - 'comfortable' or 'compact'.
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
   * @param {string} mode - 'fill' or 'border'.
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
   * @param {boolean} on - Whether highlighting is enabled.
   * @returns {void}
   * @example
   * applyHighValue(card, true);
   */
  function applyHighValue(card, on) {
    card.classList.toggle("highvalue-on", !!on);
  }

  /**
   * Filter items in a user card by type, search query, and value.
   *
   * @param {HTMLElement} card - User card element.
   * @param {string} filter - Active filter name.
   * @param {string} [query] - Search query string.
   * @returns {void}
   * @example
   * filterItems(card, 'strange', 'rocket');
   */
  function filterItems(card, filter, query) {
    const items = card.querySelectorAll(".item-card");
    const q = (query || "").trim().toLowerCase();
    items.forEach((it) => {
      const name = (it.dataset.name || "").toLowerCase();
      const keys = Number(it.dataset.valueKeys || 0);
      let vis = true;

      switch (filter) {
        case "unusual":
          vis = it.classList.contains("quality-unusual");
          break;
        case "strange":
          vis = it.classList.contains("quality-strange");
          break;
        case "cosmetic":
          vis = it.classList.contains("is-cosmetic");
          break;
        case "weapon":
          vis = it.classList.contains("is-weapon");
          break;
        case "dupe":
          vis = it.classList.contains("is-duplicate");
          break;
        case "attrs":
          vis = it.classList.contains("has-attrs");
          break;
        case "value":
          vis = keys >= 5;
          break; // threshold adjustable
        default:
          vis = true;
      }
      if (vis && q) vis = name.includes(q);
      it.style.display = vis ? "" : "none";
    });
  }

  /**
   * Initialize behavior and preference persistence for a user card.
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
    const densityBtn = card.querySelector(".density-toggle");
    const qualityBtn = card.querySelector(".quality-toggle");

    // restore prefs
    const density =
      localStorage.getItem(LS_KEYS.density(steamid)) || "comfortable";
    const quality = localStorage.getItem(LS_KEYS.quality(steamid)) || "fill";
    const hv = localStorage.getItem(LS_KEYS.hv(steamid)) === "on";
    const savedFilter = localStorage.getItem(LS_KEYS.filter(steamid)) || "all";
    const savedSearch = localStorage.getItem(LS_KEYS.search(steamid)) || "";

    applyDensity(card, density);
    applyQuality(card, quality);
    applyHighValue(card, hv);
    if (search) {
      search.value = savedSearch;
    }

    // apply initial filter
    if (chips.length) {
      chips.forEach((c) =>
        c.classList.toggle("is-active", c.dataset.filter === savedFilter),
      );
      filterItems(card, savedFilter, savedSearch);
    }

    // handlers
    densityBtn?.addEventListener("click", () => {
      const next = card.classList.contains("density-compact")
        ? "comfortable"
        : "compact";
      localStorage.setItem(LS_KEYS.density(steamid), next);
      applyDensity(card, next);
    });

    qualityBtn?.addEventListener("click", () => {
      const next = card.classList.contains("quality-border")
        ? "fill"
        : "border";
      localStorage.setItem(LS_KEYS.quality(steamid), next);
      applyQuality(card, next);
    });

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

    // horizontal scroll enhancements
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

      let dragging = false,
        startX = 0,
        startLeft = 0;
      itemsWrap.addEventListener("mousedown", (e) => {
        dragging = true;
        startX = e.clientX;
        startLeft = itemsWrap.scrollLeft;
        itemsWrap.classList.add("is-dragging");
      });
      window.addEventListener("mousemove", (e) => {
        if (!dragging) return;
        itemsWrap.scrollLeft = startLeft - (e.clientX - startX);
      });
      window.addEventListener("mouseup", () => {
        dragging = false;
        itemsWrap.classList.remove("is-dragging");
      });
    }
  }

  /**
   * Attach UI behavior to all uninitialized user cards.
   *
   * @returns {void}
   */
  function attachUI() {
    document.querySelectorAll(".user-card.user-box").forEach((card) => {
      if (card.dataset.uiInit === "1") return;
      card.dataset.uiInit = "1";
      initCardBehavior(card);
    });
  }

  // Run on initial load and whenever new cards are appended
  /**
   * Entry point to bind UI features.
   * @returns {void}
   */
  function runAttach() {
    attachUI();
  }

  // integrate with existing attachHandlers hook if present
  if (window.attachHandlers) {
    const old = window.attachHandlers;
    window.attachHandlers = function () {
      old();
      runAttach();
    };
  }

  document.addEventListener("DOMContentLoaded", runAttach);
})();
