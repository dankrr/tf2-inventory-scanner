# TODO Checklist

## UI / UX Improvements
- [x] Convert `index.html` to Bootstrap 5 layout with cards and responsive grid
- [x] Add loading spinner during inventory scanning
- [x] Replace quality backgrounds with quality-colored borders
- [x] Improve font hierarchy and spacing
- [x] Ensure mobile-friendly layout

## ID Input and Resolution
- [x] Resolve SteamID2, SteamID3, and vanity URLs to SteamID64
- [x] Filter out invalid ID lines
- [x] Remove duplicates and trim whitespace before processing
- [x] Handle up to 20 SteamIDs per submission

## Backend Enhancements
- [x] Map defindex to item names in `inventory_processor.py`
- [ ] Optionally cache item schema locally
- [x] Show "Private Inventory" error on 403/400 responses
- [x] Use placeholder image if `icon_url` missing
- [ ] Batch profile lookups when possible

## Optional Feature: Item Valuation
- [ ] Use Backpack.tf price API to fetch item values
- [ ] Display item value next to name and sort by value

## Deployment Enhancements
- [x] Add `Procfile` for Heroku
- [x] Add `Dockerfile`
- [x] Add optional deployment config for Render/Fly.io
- [x] Add `.gitignore` for `/__pycache__/`, `/.venv/`, `.env`

## Bonus
- [x] Tests for SteamID conversion logic
- [x] Sample inventory JSON for UI testing
- [x] Log timeouts and API failures in console

