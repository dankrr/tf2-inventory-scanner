(function (global) {
  let initialized = false;
  let closeTimer = null;

  /**
   * Retrieve the item modal element.
   * @returns {HTMLDialogElement|null} Modal dialog or null if missing.
   * @example
   * const modal = getModal();
   */
  function getModal() {
    return document.getElementById("item-modal");
  }

  /**
   * Get the modal body container.
   * @returns {HTMLElement|null} Modal body or null.
   * @example
   * const body = getBody();
   */
  function getBody() {
    const modal = getModal();
    return modal ? modal.querySelector(".modal-body") : null;
  }

  /**
   * Display the modal dialog.
   * @returns {void}
   * @example
   * openModal();
   */
  function openModal() {
    const modal = getModal();
    if (!modal) return;
    if (closeTimer) {
      clearTimeout(closeTimer);
      closeTimer = null;
    }
    if (typeof modal.showModal === "function") {
      modal.showModal();
    } else {
      modal.style.display = "block";
    }
    modal.classList.add("open");
  }

  /**
   * Insert HTML into the modal body.
   * @param {string} html - Markup to render inside the modal.
   * @returns {void}
   * @example
   * populateModal('<p>Details</p>');
   */
  function populateModal(html) {
    const body = getBody();
    if (body) body.innerHTML = html;
  }

  /**
   * Hide the modal and clear its contents.
   * @returns {void}
   * @example
   * closeModal();
   */
  function closeModal() {
    const modal = getModal();
    if (!modal) return;
    modal.classList.remove("open");
    closeTimer = setTimeout(() => {
      if (typeof modal.close === "function") {
        modal.close();
      } else {
        modal.style.display = "none";
      }
      const body = getBody();
      if (body) body.innerHTML = "";
      closeTimer = null;
    }, 200);
  }

  /**
   * Update modal content with new HTML.
   * @param {string} html - New markup for the modal body.
   * @returns {void}
   * @example
   * updateModal('<p>Updated</p>');
   */
  function updateModal(html) {
    populateModal(html);
  }

  /**
   * Safely escape HTML entities in a string.
   * @param {string} str - Input string.
   * @returns {string} Escaped string.
   * @example
   * const safe = escapeHtml('<script>');
   */
  function escapeHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  /**
   * Build HTML representing item details for the modal.
   * @param {object} data - Item data from the backend.
   * @returns {string} Generated HTML string.
   * @example
   * const html = generateModalHTML({ name: 'Rocket Launcher' });
   */
  function generateModalHTML(data) {
    if (!data) return "";
    const esc = escapeHtml;
    const attrs = [];

    const tierMap = { 1: "Killstreak", 2: "Specialized", 3: "Professional" };
    const tierName = data.killstreak_tier
      ? tierMap[data.killstreak_tier] || data.killstreak_tier
      : null;
    const hasKsInfo = tierName || data.sheen || data.killstreak_effect;
    if (hasKsInfo) {
      let info = '<div class="killstreak-info">';
      if (tierName) {
        info += '<span class="killstreak-tier">' + esc(tierName) + "</span>";
      }
      if (data.sheen) {
        info += '<span class="sheen">';
        const bgStyle =
          data.sheen_gradient_css ||
          `background-color:${esc(data.sheen_color || "#ccc")}`;
        info +=
          `<span class="sheen-dot" style="${bgStyle}"></span>` +
          esc(data.sheen) +
          "</span>";
      }
      if (data.killstreak_effect) {
        info +=
          '<span class="killstreaker">| ' +
          esc(data.killstreak_effect) +
          "</span>";
      }
      info += "</div>";
      attrs.push(info);
    }

    if (data.unusual_effect) {
      const name =
        typeof data.unusual_effect === "object"
          ? data.unusual_effect.name
          : data.unusual_effect;
      if (name) {
        attrs.push(
          "<div><strong>Unusual Effect:</strong> " + esc(name) + "</div>",
        );
      }
    }

    [
      ["Type", data.item_type_name],
      ["Level", data.level],
      [
        "Craftable",
        typeof data.craftable === "boolean"
          ? data.craftable
            ? "Craftable"
            : "Uncraftable"
          : null,
      ],
      ["Origin", data.origin],
    ].forEach(([label, value]) => {
      if (!value) return;
      attrs.push("<div>" + esc(label) + ": " + esc(value) + "</div>");
    });

    if (data.paint_name) {
      let html = "<div>";
      if (data.paint_hex) {
        html +=
          '<span class="paint-dot" style="background:' +
          esc(data.paint_hex) +
          '"></span>';
      }
      html += "Paint: " + esc(data.paint_name) + "</div>";
      attrs.push(html);
    }

    if (data.wear_name)
      attrs.push("<div>Wear: " + esc(data.wear_name) + "</div>");

    if (data.paintkit_name)
      attrs.push("<div>Paintkit: " + esc(data.paintkit_name) + "</div>");

    if (data.crate_series_name)
      attrs.push(
        "<div>Crate series: " + esc(data.crate_series_name) + "</div>",
      );

    if (data.custom_description)
      attrs.push(
        "<div>Custom Desc: " + esc(data.custom_description) + "</div>",
      );

    let spells = "";
    if (Array.isArray(data.spells) && data.spells.length) {
      spells += '<h4 id="modal-spells">Spells</h4><ul>';
      data.spells.forEach((sp) => {
        let name = "";
        let count = null;
        if (typeof sp === "string") {
          name = sp;
        } else if (sp && typeof sp === "object") {
          name = sp.name || "";
          count = sp.count;
        } else {
          name = String(sp || "");
        }
        let line = esc(name);
        if (count && count > 1) {
          line += " (" + esc(count) + ")";
        }
        spells += "<li>" + line + "</li>";
      });
      spells += "</ul>";
    }

    if (data.id && (!data.quantity || data.quantity <= 1) && !data._hidden) {
      const url = "https://next.backpack.tf/item/" + esc(data.id);
      let link =
        '<div><a href="' +
        url +
        '" target="_blank" rel="noopener" class="history-link">History\ud83d\udd0e</a>';
      if (data.trade_hold_expires) {
        const dateStr = new Date(
          data.trade_hold_expires * 1000,
        ).toLocaleString();
        link += " Tradable after: " + esc(dateStr);
      }
      link += "</div>";
      attrs.push(link);
    }

    const details = attrs.join("") + spells;
    const imgTag =
      '<img src="' +
      esc(data.image_url || "") +
      '" width="64" height="64" alt="">';
    return imgTag + '<div id="modal-details">' + details + "</div>";
  }

  /**
   * Populate modal header fields based on item data.
   * @param {object} data - Item details.
   * @returns {void}
   */
  function updateHeader(data) {
    const title = document.getElementById("modal-title");
    const custom = document.getElementById("modal-custom-name");
    const effectBox = document.getElementById("modal-effect");

    if (title) {
      let text = "";
      if (data.killstreak_name) {
        if (["Specialized", "Professional"].includes(data.killstreak_name)) {
          text += data.killstreak_name + " Killstreak ";
        } else {
          text += data.killstreak_name + " ";
        }
      }
      text += data.display_name || data.composite_name || data.name || "";
      title.textContent = text.trim();
    }

    if (custom) custom.textContent = data.custom_name || "";
    let effectText = "";
    if (data.unusual_effect) {
      effectText =
        typeof data.unusual_effect === "object"
          ? data.unusual_effect.name || ""
          : data.unusual_effect;
    }
    if (effectBox) effectBox.textContent = effectText;
  }

  /**
   * Render badge icons in the modal header.
   * @param {Array<{icon: string, title?: string}>} badges - Badge data.
   * @returns {void}
   */
  function renderBadges(badges) {
    const box = document.getElementById("modal-badges");
    if (!box) return;
    box.innerHTML = "";
    (badges || []).forEach((b) => {
      const span = document.createElement("span");
      span.className = "badge";
      span.dataset.icon = b.icon;
      span.textContent = b.icon;
      span.title = b.title || "";
      span.addEventListener("click", () => {
        const sec = document.getElementById("modal-spells");
        if (sec) sec.scrollIntoView({ behavior: "smooth" });
      });
      box.appendChild(span);
    });
  }

  /**
   * Display a particle effect background image inside the modal.
   * @param {string|number} effectId - Particle effect identifier.
   * @returns {void}
   */
  function setParticleBackground(effectId) {
    const box = document.getElementById("modal-effect-bg");
    if (!box) return;
    if (effectId) {
      const url = "/static/images/effects/" + effectId + ".png";
      box.innerHTML = '<img src="' + url + '" alt="">';
    } else {
      box.innerHTML = "";
    }
  }

  /**
   * Populate and display the modal with provided HTML.
   * @param {string} html - Markup to show.
   * @returns {void}
   * @example
   * showItemModal('<p>Hello</p>');
   */
  function showItemModal(html) {
    if (!html) {
      console.warn("Empty modal HTML!");
      return;
    }
    populateModal(html);
    openModal();
  }

  /**
   * Attach modal event handlers and enable closing behaviors.
   * @returns {void}
   * @example
   * initModal();
   */
  function initModal() {
    if (initialized) return;
    const modal = getModal();
    if (!modal) return;

    // NEW: header close button
    const closeBtn = modal.querySelector(".modal-close");
    if (closeBtn) closeBtn.addEventListener("click", closeModal);

    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeModal();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
    });
    initialized = true;
  }

  global.modal = {
    initModal,
    openModal,
    closeModal,
    populateModal,
    renderBadges,
    showItemModal,
    generateModalHTML,
    updateHeader,
    setParticleBackground,
  };
})(window);
