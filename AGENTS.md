# AGENTS.md

## Project Summary

TF2 Inventory Scanner is an async-capable Flask web application. Users submit one or more Steam IDs in any supported format; the app resolves each to a SteamID64, fetches the TF2 inventory, enriches items with backpack.tf prices, and renders a card per user showing:

- Steam username and avatar (links to Steam profile)
- TF2 playtime in hours
- Item cards with name, image, quality, wear, price, and special attributes
- Graceful error messages for private inventories or Steam downtime

---

## Repository Layout

```
app.py                  Flask application, routes, and async orchestration
run.py                  Entry point (thin wrapper around app.py)
utils/
  steam_api_client.py   Steam ID parsing and all Steam Web API calls
  inventory_processor.py  Top-level pipeline: raw inventory → enriched items
  inventory/            Sub-package with per-attribute enrichment modules
  valuation_service.py  Price lookup and formatting (ref / keys / USD)
  price_loader.py       Ensures price and currency caches exist on disk
  price_service.py      Low-level backpack.tf price data access
  schema_provider.py    Loads and caches the TF2 item schema from autobot.tf
  local_data.py         Reads static JSON data files at startup
  cache_manager.py      Cache validation, refresh, and fault-tolerance logic
  constants.py          Static mappings (paint colors, sheens, killstreak tiers…)
  wear_helpers.py       Wear tier decoding and seed parsing for warpaints
  helpers.py            General-purpose utility functions
  __init__.py           Public re-exports from the utils package
static/                 CSS, JS modules (submit, modal, lazy-load, retry, UI)
templates/              Jinja2 templates (index, _user, _modal, item_card)
docs/                   Extended architecture and developer documentation
scripts/                Maintenance scripts (check_legacy, validate_attributes…)
tests/                  pytest suite
```

---

## Adding New Modules

1. Place new utility modules under `utils/` (or create a top-level script for standalone tools).
2. Expose any reusable public API through `utils/__init__.py` and `__all__`.
3. All I/O-bound operations **must** use `async def` and `httpx.AsyncClient`.
4. Add tests under `tests/` and update relevant documentation in `docs/`.
5. Run `pre-commit` before opening a pull request.

---

## Supported Steam ID Formats

| Format | Example |
|---|---|
| SteamID64 | `76561197960287930` |
| SteamID2 | `STEAM_0:0:11101` |
| SteamID3 | `[U:1:22202]` |
| Vanity URL | `gaben` |
| TF2 `status` dump | multi-line server console output |

### Parsing rules

- Only `[U:1:########]` tokens are accepted from `status` output.
- Lines containing `[A:1:...]`, `map:`, usernames, or no valid ID are silently ignored.
- All formats are normalised to SteamID64 before any API call.
- Use `sac.convert_to_steam64()` for conversion; `sac.extract_steam_ids()` for bulk parsing.

---

## External APIs

### Steam API (`STEAM_API_KEY` required)

| Endpoint | Purpose |
|---|---|
| `ISteamUser/ResolveVanityURL` | Vanity URL → SteamID64 |
| `ISteamUser/GetPlayerSummaries` | Username, avatar, profile URL |
| `IPlayerService/GetOwnedGames` | TF2 playtime (appid 440) |
| `IEconItems_440/GetPlayerItems/v0001` | TF2 inventory items |

The inventory endpoint returns `status: 1` for a public inventory and `status: 15` for a private or empty one.

### backpack.tf API (`BPTF_API_KEY` required)

- `https://backpack.tf/api/IGetPrices/v4` — item prices in refined metal
- `https://backpack.tf/api/IGetCurrencies/v1` — key and refined metal exchange rates

### TF2 Item Schema

- `https://schema.autobot.tf/raw/schema/items` — cached locally by `SchemaProvider`

---

## Application Flow

1. User submits one or more Steam IDs via the web form or `POST /api/users`.
2. `extract_steam_ids()` parses the raw input; `convert_to_steam64()` normalises each ID.
3. One `asyncio.Task` is created per unique SteamID64.
4. `asyncio.gather()` runs all tasks concurrently:
   - `get_player_summaries_async()` — username, avatar, profile URL
   - `get_tf2_playtime_hours_async()` — TF2 hours
   - `fetch_inventory_async()` → `inventory_processor.process_inventory()` — enriched items
5. Duplicate items are merged into quantity stacks by `stack_items()`.
6. `render_template("_user.html", user=…)` produces one HTML snippet per user.
7. Completed and failed users are returned as separate lists.

---

## Async Conventions

- All I/O-bound functions use `async def` and `httpx.AsyncClient` with explicit timeouts.
- Batch operations use `asyncio.gather()` or `asyncio.create_task()`.
- Do **not** call `asyncio.run()` inside route handlers; Flask's async support handles the event loop.
- Avoid spawning nested event loops.

---

## Development Guide

- Keep route handlers in `app.py` thin — delegate logic to `utils/`.
- Do **not** modify `image_url` or layout-critical template variables without updating all templates.
- Raise `ValueError` early if required environment variables (`STEAM_API_KEY`) are missing.
- Prices are loaded once at startup and shared across all requests; do not re-fetch per request.
- `local_data.load_files()` must be called before any code that reads constants or schema data.

---

## Testing

```bash
pip install -r requirements-test.txt
pytest
```

- Use `pytest-asyncio` for async route and helper tests.
- Simulate TF2 `status` output as multi-line string input in parser tests.
- Test cases must cover: invalid IDs, private inventories, missing API keys, and empty inventories.
- Run `python scripts/check_legacy.py` to catch leftover legacy cache files before pushing.

---

## Security

- API keys are never rendered into HTML or exposed to client-side JavaScript.
- Always read keys via `os.getenv()`.
- Display a fallback UI message when required keys are absent rather than crashing silently.

---

## Contributor Setup

```bash
# Install dev dependencies
pip install -r requirements-test.txt

# Install pre-commit hooks (runs on every commit)
pre-commit install

# Run hooks manually before pushing
pre-commit run --files <changed files>
python scripts/check_legacy.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

---

## Documentation Standards

- Use ATX headings (`#`, `##`, …) in all Markdown files.
- Wrap all code examples in fenced code blocks with a language tag.
- Place screenshots and diagrams in `docs/images/` and reference them with relative paths.
- Run `pre-commit` after editing documentation to apply linting.

---

## Role of This Document

`AGENTS.md` is the authoritative style and architecture reference for both human contributors and any automated tooling working on this repository. Consult it when adding new modules, extending existing utilities, or onboarding to the project.
