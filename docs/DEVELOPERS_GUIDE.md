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

- Unusual effect icons use empty alt text, ignore pointer events so modals remain clickable, and a small helper removes the image if loading fails.
