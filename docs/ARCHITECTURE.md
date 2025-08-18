# Architecture Overview

This project is an async-enabled Flask application that scans Team Fortress 2 inventories.
The frontend renders two result buckets:

- **Completed** – successful inventory scans
- **Failed** – scans that could not be processed

New results are appended to the appropriate bucket. The Completed bucket keeps
public results ahead of private ones, ensuring private inventories collect at
the bottom. When the user is not at the bottom of the page, a floating
"New results — Jump ↓" button appears to quickly navigate to the latest results.
Two compact floating buttons in the lower-right corner provide quick access to
refresh failed inventories or scroll back to the top.
A floating gear button in the lower-left now exposes display settings, allowing
users to toggle compact and border modes without relying on legacy header
buttons.

The server exposes REST endpoints for initiating scans and retrying failed ones.
Client-side JavaScript handles form submission, retry flows, and dynamic UI updates.
The Steam ID input auto-focuses on load via HTML `autofocus` with a JavaScript
fallback to ensure it's ready for pasting immediately.
`static/ui.js` adds per-user inventory search with sticky headers and provides global
toggles for compact density and border-only quality modes, both persisted via
`localStorage` and reflected through `aria-pressed` states and descriptive titles for accessibility.

Legacy header toggles are hidden in favor of the new floating settings menu,
which synchronizes with the existing body classes and keeps display options
accessible on all layouts.
Uncraftable items rely solely on a dashed quality border without the previous inner gray ring.
Sticky user headers now isolate their stacking context so they remain above item cards and prices while scrolling.
Each `.item-wrapper` now includes a `data-name` attribute so client-side scripts can filter items by name. `static/retry.js` rebinds these per-user searches after inventory refreshes, caching item names and handling legacy and new inventory containers.

Item cards no longer render inline titles, keeping the grid clean; names appear only in the modal. Unusual effect icons are decorative overlays that ignore pointer events, and a JavaScript fallback removes the icon if it fails to load. Modal clicks are delegated from result containers so dynamically added cards remain interactive.

Card media sit inside an `.item-media` wrapper that centers the main icon while keeping particle overlays behind it; failed effect images remove themselves to avoid broken placeholders.
