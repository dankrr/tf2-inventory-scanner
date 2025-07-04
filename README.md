# TF2 Inventory Scanner ![CI](https://github.com/dankrr/tf2-inventory-scanner/actions/workflows/ci.yml/badge.svg) [![coverage](https://codecov.io/gh/dankrr/tf2-inventory-scanner/branch/main/graph/badge.svg)](https://codecov.io/gh/dankrr/tf2-inventory-scanner)

## Overview

A Flask web app that inspects one or more Steam users' Team Fortress 2 inventories. It accepts **SteamID64**, **SteamID3**, **SteamID2**, and **vanity URLs**, resolves them to SteamID64, and enriches the inventory using the Steam Web API and cached item schema.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt -r requirements-test.txt
   ```
2. Copy the example environment file and set your API key:
   ```bash
   cp .env.example .env
   # edit .env and set STEAM_API_KEY=<your key>
   ```
   The app uses **python-dotenv** to load variables at runtime.

## Usage

Run the application locally and open `http://localhost:5000` in your browser:
```bash
python app.py
```
Submit any supported SteamID format. Each user panel shows the avatar, TF2 playtime, and an item grid.

## Development

- Templates live under `templates/`; `index.html` includes `_user.html` for each user.
- Item schema is cached automatically via `SchemaProvider` in
  `utils/schema_provider.py`. Pass `base_url` to use a mirror. Update it with:
  ```bash
  python app.py --refresh  # fetch latest schema files
  python main.py --refresh
  # verbose output is enabled automatically; no --verbose flag required
  ```
- Inspect a single user's inventory from the command line (defaults to a demo
  ID if omitted):
  ```bash
  python main.py <steamid>
  ```
- Use `--test` to run offline against cached data.
- Access schema properties directly:
  ```python
  from utils.schema_provider import SchemaProvider

  provider = SchemaProvider()
  qualities = provider.get_qualities()
  ```
You can also enrich raw inventory items using `ItemEnricher`:
```python
from utils.item_enricher import ItemEnricher

enricher = ItemEnricher(provider)
items = enricher.enrich_inventory(raw_items)
```

## Modals

All modal behaviour is centralized in `static/modal.js`. Other scripts use
its helper functions and should never manipulate the modal DOM directly.
Use `showItemModal(html)` to populate and display the dialog.

## Testing

Run linting and tests before committing:
```bash
pre-commit run --all-files
pytest --cov=utils --cov=app
```
HTML coverage is written to `htmlcov/`.

## Docker / Deployment

Build and run the container locally:
```bash
docker build -t tf2-scanner .
docker run -p 5000:5000 tf2-scanner
```
The server can also be accessed on your LAN.
