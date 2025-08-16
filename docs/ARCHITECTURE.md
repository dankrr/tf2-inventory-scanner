# Architecture Overview

This project is an async-enabled Flask application that scans Team Fortress 2 inventories.
The frontend renders two result buckets:

- **Completed** – successful inventory scans
- **Failed** – scans that could not be processed

New results are appended to the bottom of the appropriate bucket without reordering
existing cards. When the user is not at the bottom of the page, a floating
"New results — Jump ↓" button appears to quickly navigate to the latest results.

The server exposes REST endpoints for initiating scans and retrying failed ones.
Client-side JavaScript handles form submission, retry flows, and dynamic UI updates.

## Client UI Enhancements

Each user card renders a sticky header with search, filter chips, and a sort
selector. Global density and quality toggles placed next to the form actions
affect all user cards. Search, filters, and sorting operate per user and persist
in `localStorage`. Item filtering and sorting work on `.item-wrapper` elements
that encapsulate both the card and price chip, and sorting reattaches wrappers
in small batches via `requestAnimationFrame` for smoother updates. Behavior is
managed by `static/ui.js`.
