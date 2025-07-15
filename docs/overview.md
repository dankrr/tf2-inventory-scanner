# Repository Overview

This document provides a high-level summary of the TF2 Inventory Scanner codebase. It explains where the application starts, which utilities are involved and how the templates and static files work together.

## Main Entry Point

- **`run.py`** defines an async `main()` function that launches the Hypercorn server. It binds to the configured port, optionally runs in test mode and finally serves the Flask app.
- **`app.py`** sets up the Flask application, loads environment variables and implements the route handlers. The index route accepts Steam IDs, fetches profile data and inventories asynchronously and renders `index.html`.

```python
# run.py
async def main() -> None:
    port = int(os.getenv("PORT", 5000))
    kill_process_on_port(port)
    if ARGS.test:
        await _setup_test_mode()
    config = Config()
    config.bind = [f"0.0.0.0:{port}"]
    config.use_reloader = not ARGS.test
    await serve(app, config)
```

## Utility Modules

- **`utils/id_parser.py`** – Extracts valid Steam ID tokens from free‑form text.
- **`utils/steam_api_client.py`** – Wraps Steam Web API calls for player summaries, inventories and playtime. Provides sync and async helpers.
- **`utils/inventory_processor.py`** – Enriches inventory items with schema data, price lookups, wear information and more.
- **`utils/price_loader.py`** – Downloads Backpack.tf price and currency dumps and caches them locally.
- **`utils/price_service.py`** – Formats raw price values into readable strings.
- **`utils/valuation_service.py`** – Builds a price map and exposes helpers to attach price info to items.
- **`utils/local_data.py`** – Loads cached schema files and constant mappings such as paints and qualities.
- **`utils/schema_provider.py`** – Fetches and caches TF2 schema data from `schema.autobot.tf`.

## Templates

- **`templates/index.html`** – Main page containing the form to submit Steam IDs and the container that holds user cards.
- **`templates/_user.html`** – Renders a user card with profile details and inventory grid.
- **`templates/item_card.html`** – Displays a single inventory item with icons and price information.
- **`templates/_modal.html`** – Small snippet used by `modal.js` to show item details in a dialog.

## Static Assets

- **CSS**: `static/style.css` contains the dark theme and layout for the page.
- **JavaScript**:
  - `static/submit.js` handles form submission and dynamic loading of user cards.
  - `static/retry.js` allows retrying failed scans.
  - `static/lazyload.js` implements image lazy loading.
  - `static/modal.js` powers the item detail dialog.
- **Images**: Stored under `static/images/` with effect icons in `static/images/effects/` and logos in `static/images/logos/`.
- **Configuration**: `static/exclusions.json` lists item origins that should be hidden and craft‑weapon exclusions. See `docs/exclusions.md` for details.

## How Everything Fits Together

1. Input text is parsed with `extract_steam_ids()` to collect valid Steam IDs.
2. For each ID, the app fetches profile summaries, playtime and inventory data asynchronously via `steam_api_client`.
3. `inventory_processor.process_inventory()` enriches each item with schema details and pricing via `valuation_service`.
4. User cards are rendered server‑side using `_user.html` and `item_card.html` and inserted into `index.html`.
5. JavaScript enhances the page with lazy loading, modal dialogs and retry functionality.
6. Price and schema data are cached under `cache/` to speed up processing and reduce network calls.

