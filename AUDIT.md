# Redundancy Audit & Workflow Map

## 1. Redundancy / Dead Code Audit

Below is an overview of the repository. Each file or function is marked as:

- ✅ **in use** – referenced by the app or tests
- ⚠ **possible duplicate** – similar functionality exists elsewhere
- 🗑 **safe to delete** – no references found

### Observations

- `convert.py` and `convert_from_getplayeritems.py` both transform Steam `GetPlayerItems` JSON to the community inventory format. Neither is used by the Flask app or tests.
- `translate_and_enrich.py` implements inventory enrichment logic that overlaps with `utils/inventory_processor.py`.
- `inventory_scanner.py` is a small CLI helper that duplicates `utils/steam_api_client.fetch_inventory`.
- `enrich_autobot.py` fetches mapping data from an external service. It is not imported anywhere else.

## 2. Workflow Map

```
User submits form → `app.py:index()` →
  `utils.id_parser.extract_steam_ids` parses IDs →
  `utils.steam_api_client.convert_to_steam64` normalises each ID →
  for each SteamID64:
    `app.build_user_data_async`
      ↳ `steam_api_client.fetch_inventory`
      ↳ `utils.inventory_processor.enrich_inventory`
      ↳ `steam_api_client.get_player_summaries`
      ↳ `steam_api_client.get_tf2_playtime_hours`
    Render `_user.html` with enriched items
  `templates/index.html` inserts the user cards via JS (`static/retry.js`)
```

## 3. File-by-file Reference Table

| Path | Purpose | Key symbols / templates | Entry point | Status |
| --- | --- | --- | --- | --- |
| `app.py` | Flask application handling form input and rendering results | `index`, `build_user_data_async` | `python app.py` | ✅ |
| `inventory_scanner.py` | CLI to fetch a single user's inventory | `fetch_inventory`, `main` | `python inventory_scanner.py` | ⚠ |
| `convert.py` | Convert `GetPlayerItems` JSON to community format | `convert_getplayeritems` | standalone script | 🗑 |
| `convert_from_getplayeritems.py` | Alternative converter script | `convert_getplayeritems_to_community` | standalone script | 🗑 |
| `translate_and_enrich.py` | Standalone enrichment utility, overlaps with `utils/inventory_processor.py` | `enrich_inventory` | `python translate_and_enrich.py` | ⚠ |
| `enrich_autobot.py` | Fetches mapping data from `autobot.tf` into JSON files | `fetch_all` | `python enrich_autobot.py` | 🗑 |
| `utils/steam_api_client.py` | Steam Web API helpers and ID conversion | `get_player_summaries`, `fetch_inventory`, `convert_to_steam64`, `get_tf2_playtime_hours` | imported by app | ✅ |
| `utils/inventory_processor.py` | Enriches inventory items using schema data | `enrich_inventory`, `process_inventory` | imported by app | ✅ |
| `utils/items_game_cache.py` | Handles `items_game` caching | `ensure_future`, `load_items_game_cleaned` | imported by app | ✅ |
| `utils/schema_fetcher.py` | Downloads TF2 item schema | `ensure_schema_cached`, `refresh_schema` | imported by app | ✅ |
| `utils/local_data.py` | Loads local cache files | `load_files`, `clean_items_game` | imported by app | ✅ |
| `utils/id_parser.py` | Extracts valid SteamID tokens from text | `extract_steam_ids` | imported by app | ✅ |
| `templates/index.html` | Main HTML page | form for IDs, `user-container` | Flask template | ✅ |
| `templates/_user.html` | Partial user card template | uses `user.*` fields | Flask template | ✅ |
| `static/retry.js` | Client-side retry/DOM helper | `refreshCard` | loaded by HTML | ✅ |
| `static/style.css` | Stylesheet | n/a | loaded by HTML | ✅ |
| `static/img/steam_logo.svg` | Logo icon | n/a | used in template | ✅ |
| `data/items_game_cleaned.json` | Sample cleaned schema data | n/a | used in tests | ✅ |
| `cached_inventories/*.json` | Example cached inventories for offline mode | n/a | optional | ✅ |
| `fixed.json`, `full_inventory.json` | Example inventory dumps | n/a | none | 🗑 |
| Tests under `tests/` | Pytest suite covering utilities and templates | various | `pytest` | ✅ |

## 4. Conclusion

Most active logic resides in `app.py` and `utils/`. The converter and enrichment scripts (`convert.py`, `convert_from_getplayeritems.py`, `translate_and_enrich.py`, `inventory_scanner.py`, `enrich_autobot.py`) are not required for normal app operation and can be removed or consolidated.
