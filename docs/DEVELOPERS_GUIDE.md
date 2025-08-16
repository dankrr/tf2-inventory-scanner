# Developer Guide

- Follow JSDoc conventions for all JavaScript functions.
- Inventory scan results are split into **Completed** and **Failed** buckets.
  Always append new cards to the bottom of the appropriate bucket.
- Use `addCardToBucket` when adding or moving cards so scroll and jump
  behavior remains consistent.
- Run the commands listed in `docs/COMMANDS.md` before committing changes.
- Per-user UI behavior lives in `static/ui.js`. Call `attachHandlers()` after
  adding new cards so search, filters, and other features initialize.
