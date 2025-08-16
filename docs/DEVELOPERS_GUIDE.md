# Developer Guide

- Follow JSDoc conventions for all JavaScript functions.
- Inventory scan results are split into **Completed** and **Failed** buckets.
  Always append new cards to the bottom of the appropriate bucket.
- Use `addCardToBucket` when adding or moving cards so scroll and jump
  behavior remains consistent.
- Run the commands listed in `docs/COMMANDS.md` before committing changes.
- UI helpers live in `static/ui.js`. Extend `window.attachHandlers` when adding
  dynamic elements so new cards receive search and modal behavior.
- Global toggle buttons should update `aria-pressed` and `title` attributes for
  accessibility; follow the pattern in `updateToggleButtons`.
- Item cards omit inline titles; names surface only within the modal.
- Modal clicks are delegated from result containers. Ensure overlays and badges do not capture pointer events.
- Unusual effect icons use empty alt text, ignore pointer events, and a helper removes the image if loading fails.
- Wrap icon elements in `.item-media` to center content and place particle overlays behind; include `onerror="this.remove()"` on effect images so missing assets vanish cleanly.
