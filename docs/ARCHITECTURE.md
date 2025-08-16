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

Each user card renders a sticky header with search, density and quality toggles.
Filter chips and a quick search box allow per-user item filtering and horizontal
scroll improvements. Preferences persist in `localStorage` and behavior is
managed by `static/ui.js`.
