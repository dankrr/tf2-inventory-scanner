# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- Pre-commit configuration for formatting, linting, and secret scanning.
- Locked dependencies and instructions for secure updates.
- Additional unit tests for inventory processing and ID conversion.
- SchemaProvider class for fetching schema properties.
- Paintkits endpoint cached as `warpaints.json`.

### Removed
- GitHub Actions workflow and Codecov configuration.

### Changed
- Updated schema caching logic and UI (previous releases).
- Security audit using git-secrets and pip-audit.
- Price loader now reads both Craftable and Non-Craftable price entries.
