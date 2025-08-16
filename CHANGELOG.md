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
- Sticky inventory headers, per-user search, filters, and toggles with updated docs.

### Removed

- GitHub Actions workflow and Codecov configuration.

### Changed

- Updated schema caching logic and UI (previous releases).
- Security audit using git-secrets and pip-audit.
- Price loader now reads both Craftable and Non-Craftable price entries.
- Plain craft weapons from achievements or promotions are no longer filtered and
  such items are hidden without price data.
- Untradable timed-drop items are now marked as hidden.

## [2025-08-15]

### Added

- Separated scan results into Completed and Failed buckets with a jump-to-new-results button.
- Updated client scripts with JSDoc comments and synchronized project documentation.
  2025-08-16 - Added sticky inventory headers, per-user search and filters, and documentation sync.
