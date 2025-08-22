# Developer Guide

- Follow JSDoc conventions for all JavaScript functions.
- Inventory scan results are split into **Completed** and **Failed** buckets.
  The Completed bucket keeps public cards before private ones.
- Use `addCardToBucket` when adding or moving cards so ordering, scroll,
  and jump behavior remains consistent.
- Run the commands listed in `docs/COMMANDS.md` before committing changes.
- Inventory enrichment helpers reside under `utils/inventory/`; import from these
  modules instead of the legacy `inventory_processor` monolith.
- Each enriched item now includes additive flags `is_unusual`,
  `unusual_effect_id`, `unusual_effect_name`, `is_strange`, and an
  `extra_qualities` list derived purely from attributes and quality id.
- UI helpers live in `static/ui.js`. Extend `window.attachHandlers` when adding dynamic elements so new cards receive search and modal behavior, including the `attachUserSearch` filter.
- Floating scroll-to-top and refresh controls are initialized by `setupFloatingControls`; call it after DOM load.
- Global toggle buttons should update `aria-pressed` and `title` attributes for
  accessibility; follow the pattern in `updateToggleButtons`.
- Display settings now live behind a floating gear menu initialized by `setupSettingsFab()`.
  Legacy header toggles are hard-hidden by CSS, and any header icons are copied into the menu via `syncSettingsIconsFromLegacy()`.
- Font Awesome icons are injected by `setFAIcons` to standardize the gear, Compact, and Border Mode menu symbols.
- Item cards omit inline titles; names surface only within the modal.
- Uncraftable items rely on dashed borders only; the inner gray ring has been removed to reduce visual clutter.
- Modal clicks are delegated from result containers. Ensure overlays and badges do not capture pointer events.
- Unusual effect icons use empty alt text, ignore pointer events, and a helper removes the image if loading fails.
- Unusual items take precedence over decorated styling; when an item is Unusual or a decorated weapon with an unusual effect, apply `quality-unusual` and `border-unusual` classes and omit dual-quality accents.
- Wrap icon elements in `.item-media` to center content and place particle overlays behind; include `onerror="this.remove()"` on effect images so missing assets vanish cleanly.
