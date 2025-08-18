# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- Pre-commit configuration for formatting, linting, and secret scanning.
- Locked dependencies and instructions for secure updates.
- Additional unit tests for inventory processing and ID conversion.
- SchemaProvider class for fetching schema properties.
- Paintkits endpoint cached as `warpaints.json`.
- Async Flask routes with `httpx` replacing `requests` for concurrent HTTP calls.
- IntersectionObserver-based image lazy loading script.
- Documentation moved to `docs/` with a detailed workflow guide.
- License changed to an MIT-style Non-Commercial license.

### Removed

- GitHub Actions workflow and Codecov configuration.

### Changed

- Updated schema caching logic and UI (previous releases).
- Security audit using git-secrets and pip-audit.
- Price loader now reads both Craftable and Non-Craftable price entries.
- Plain craft weapons from achievements or promotions are no longer filtered and
  such items are hidden without price data.
- Untradable timed-drop items are now marked as hidden.

- [2025-08-17] - Completed bucket now keeps public cards before private ones. Documentation synchronized.

- [2025-08-17] - Added floating top and refresh controls with synchronized documentation and JSDoc.
- [2025-08-16] - Centered card media within `.item-media` and removed missing effect icons. Documentation synchronized.
- [2025-08-16] - Restored item modal clicks and added JS fallback to remove missing effect icons. Documentation synchronized.
- [2025-08-16] - Delegated item modal clicks, removed card titles, and synchronized documentation.
- [2025-08-16] - Use single quotes for serialized item data to avoid HTML issues. Documentation synchronized.

## [2025-08-16]

### Added

- Accessibility and pressed-state styling for Compact and Border mode buttons.
- Synchronized documentation and JSDoc for updated UI behavior.
- Isolated stacking contexts so sticky user headers render above item content.
- Added per-user inventory search binding and item `data-name` attributes for filtering.
- Enhanced search to cache item names and support legacy/new inventory containers.
- Synchronized documentation and JSDoc comments.

## [2025-08-15]

### Added

- Separated scan results into Completed and Failed buckets with a jump-to-new-results button.
- Updated client scripts with JSDoc comments and synchronized project documentation.

## [2025-08-16]

### Changed

- Removed inner gray ring from uncraftable item cards, relying solely on the dashed quality border.
- Synchronized documentation.

## [2025-05-11]

### Added

- Sticky user headers with per-user search.
- Global Compact and Border mode toggles with persistence.
- Documentation and JSDoc synchronization.

## [2025-08-17]

### Changed

- Precompute full item titles for tooltip and remove redundant inline names.

### Fixed

- Restore single quotes on item cards and guard modal against malformed `data-item`.
- Synchronized documentation.

## [2025-08-18]

### Added

- Autofocus attribute and JS fallback to focus the Steam IDs input on load.

### Fixed

- Synchronized documentation.

## [2025-08-18]

### Added

- Modal header close button with glass-styled layout.
- JSDoc comments for modal utilities.

### Fixed

- Synchronized documentation.

## [2025-08-18]

### Added

- Robust modal/backdrop manager that prevents stuck overlays and recenters on resize.

### Fixed

- Ensured modal backdrop fades out cleanly and documentation remains synced.

## [2025-08-18]

### Added

- Modal backdrop and placement helpers with centered desktop panel and mobile bottom sheet.

### Fixed

- Synchronized documentation.
