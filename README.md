# TF2 Inventory Scanner ![CI](https://github.com/dankrr/tf2-inventory-scanner/actions/workflows/ci.yml/badge.svg) [![coverage](https://codecov.io/gh/dankrr/tf2-inventory-scanner/branch/main/graph/badge.svg)](https://codecov.io/gh/dankrr/tf2-inventory-scanner)

## Overview

An async-enabled Flask 3 web app that inspects one or more Steam users' Team Fortress 2 inventories. It accepts **SteamID64**, **SteamID3**, **SteamID2**, and **vanity URLs**, resolves them to SteamID64, and enriches the inventory using the Steam Web API and cached item schema. All routes are `async def` functions and HTTP calls are made with `httpx`.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt  # brings in Flask[async] and httpx
   pip install -r requirements-test.txt  # includes pytest-cov
   pip install pre-commit
   ```
2. Copy the example environment file and set your API key:
   ```bash
   cp .env.example .env
   # edit .env and set STEAM_API_KEY=<your key>
   # and BPTF_API_KEY=<your backpack.tf key>
   ```
   The app uses **python-dotenv** to load variables at runtime.

## Usage

Run the application locally and open `http://localhost:5000` in your browser:
```bash
python app.py  # Flask 3 will run the async routes
```
Submit any supported SteamID format. Each user panel shows the avatar, TF2 playtime, and an item grid.

Example using the JSON API:
```bash
curl -X POST http://localhost:5000/api/users \
  -H 'Content-Type: application/json' \
  -d '{"ids": ["76561197960435530"]}'
```

## Development

- Templates live under `templates/`; `index.html` includes `_user.html` for each user.
- Item schema is cached automatically via `SchemaProvider` in
  `utils/schema_provider.py`. Paintkit names are written to
  `cache/schema/warpaints.json`. Pass `base_url` to use a mirror. Update it with:
  ```bash
  python app.py --refresh  # fetch latest schema files (shows progress)
  python main.py --refresh
  ```
- Inspect a single user's inventory from the command line (defaults to a demo
  ID if omitted):
  ```bash
  python main.py <steamid>
  ```
 - Use `--test` to run offline against cached data. The last SteamID entered is
   saved to `cached_inventories/last.txt` and you'll be prompted to reuse it on
   subsequent runs.
- List warpaints present in cached inventories:
  ```bash
  python scripts/list_warpaints.py
  ```
- Access schema properties directly:
  ```python
  from utils.schema_provider import SchemaProvider

  provider = SchemaProvider()
  qualities = provider.get_qualities()
  ```
Before enriching inventories, load the cached schema to populate
`ITEMS_BY_DEFINDEX`:
```python
from utils import local_data

local_data.load_files(verbose=True)
```
You can also enrich raw inventory items using `ItemEnricher`:
```python
from utils.item_enricher import ItemEnricher

enricher = ItemEnricher(provider)
items = enricher.enrich_inventory(raw_items)
```
Or manually apply schema info via `ITEMS_BY_DEFINDEX`:
```python
for asset in raw_items:
    entry = local_data.ITEMS_BY_DEFINDEX.get(int(asset["defindex"]), {})
    asset["name"] = entry.get("item_name") or entry.get("name")
```

## Modals

All modal behaviour is centralized in `static/modal.js`. Other scripts use
its helper functions and should never manipulate the modal DOM directly.
Use `showItemModal(html)` to populate and display the dialog.

## Lazy Loading

Item images and unusual effect overlays are lazily loaded via
`static/lazyload.js`. The script uses `IntersectionObserver` to replace each
image's `data-src` attribute with `src` only when the card scrolls into view.
This avoids downloading hundreds of images on page load while keeping the
markup simple.

## Spells

Halloween spell detection now relies on a static map of known spells. For each
item attribute with a defindex from `1004` to `1009`, the numeric value is
matched against this table to produce the spell name. No schema lookups are
required and spell names are always resolved offline.

## Testing

Run linting and tests before committing:
```bash
pre-commit run --all-files
pytest --cov=utils --cov=app
```
HTML coverage is written to `htmlcov/`.

## Test Suite

Running the full test suite requires the additional packages listed in
`requirements-test.txt`. Install them alongside the main requirements before
invoking `pytest`. CI runs tests with coverage options, so the `pytest-cov`
plugin must be available (it's included in `requirements-test.txt`).

Many tests also expect cached schema files under `cache/schema/`. You can refresh
these files with:

```bash
python app.py --refresh
```

## Docker / Deployment

Build and run the container locally:
```bash
docker build -t tf2-scanner .
docker run -p 5000:5000 tf2-scanner
```
The server can also be accessed on your LAN.
