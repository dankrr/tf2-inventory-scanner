# Cache Refresh Mechanics

This document explains how missing cache files are validated and refreshed when the application starts.

## Return Tuple

`fetch_missing_cache_files()` now returns three values:

```
(ok, refreshed, schema_refreshed)
```

- **`ok`** – `True` if all required cache files are present after the check.
- **`refreshed`** – `True` when any files were downloaded during refresh.
- **`schema_refreshed`** – `True` if a schema file was refreshed. The app only restarts when this is `True`.

## Schema File Detection

`SCHEMA_FILE_NAMES` contains the file names that belong to the TF2 item schema. If any of these names are missing, `_refresh_schema_concurrent()` is invoked. Pricing and currency files are refreshed separately via `ensure_prices_cached_async()` and `ensure_currencies_cached_async()`.

## Retry Behaviour

Environment variables control the retry loop:

- `CACHE_RETRIES` – how many attempts to make (default: 2).
- `CACHE_DELAY` – seconds to wait between attempts (default: 2).

During each attempt the console prints progress. After a successful refresh you will see a summary, for example:

```
✅ Cache ready: 3 files refreshed (schema: yes, pricing: no, currencies: yes)
```

If all files already exist:

```
✅ All cache files verified. No refresh needed.
```

## Restart Policy

The application restarts automatically only when `schema_refreshed` is `True`. Pricing-only updates continue without a restart.
