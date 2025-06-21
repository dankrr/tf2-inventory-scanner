# TF2 Inventory Scanner

A Flask-based web app to scan and display TF2 inventories using Steam APIs.

## Local Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Run tests with:

```bash
pytest
```

The app can optionally use a local item schema from `data/item_schema.json` to
map defindexes to item names.
