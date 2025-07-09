# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- CI workflow with lint, tests, coverage gate, and security audit.
- Pre-commit configuration for formatting, linting, and secret scanning.
- Locked dependencies and instructions for secure updates.
- Additional unit tests for inventory processing and ID conversion.
- Coverage and CI badges in the README.
- SchemaProvider class for fetching schema properties.
- Paintkits endpoint cached as `warpaints.json`.
- Wears endpoint cached as `wears.json`.

### Changed
- Updated schema caching logic and UI (previous releases).
- Security audit using git-secrets and pip-audit.
- Price loader now reads both Craftable and Non-Craftable price entries.
