# Pricing Cache Fault Tolerance

This section explains how the application now handles Backpack.tf pricing data when the API is unreachable or the cache is incomplete.

## Overview

The loader functions retry fetching prices from Backpack.tf. You can control the behavior with these environment variables:

- `PRICE_RETRIES` – number of attempts (default: `3`)
- `PRICE_DELAY` – seconds to wait between attempts (default: `5`)
- `BPTF_API_KEY` – required Backpack.tf API key

When `prices.json` exists but is smaller than **512 KB** (`EMPTY_THRESHOLD`), it is considered incomplete. The file is deleted and the loader retries the download. If all retries fail, an empty `{}` cache is written and a warning is printed.

## Startup Behavior

At launch, if pricing data cannot be fetched and the fallback empty cache is used, the console shows:

```text
⚠ Pricing unavailable (using empty cache). Inventories will show "Price: N/A".
```

The application still starts so you can browse inventories without prices.

## Refresh Handling

Running the application with `--refresh` forces a new download. Any incomplete cache is deleted before refetching. If the download still fails, the loader writes `{}` and warns the user.

## Environment Variables

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `BPTF_API_KEY` | – | Required Backpack.tf API key |
| `PRICE_RETRIES` | `3` | How many times to retry fetching prices |
| `PRICE_DELAY` | `5` | Seconds to wait between retries |

## Developer Notes

- `EMPTY_THRESHOLD` is `512 * 1024` bytes.
- Both `ensure_prices_cached` and `ensure_prices_cached_async` implement the detection and retry logic.
- Tests covering this behavior:
  - `test_timeout_creates_empty_cache`
  - `test_detect_and_delete_incomplete_cache`
  - `test_refresh_ignores_incomplete_cache`
