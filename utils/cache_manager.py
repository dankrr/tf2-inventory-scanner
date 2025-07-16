from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import List

from .price_loader import ensure_prices_cached_async, ensure_currencies_cached_async
from .schema_provider import SchemaProvider

# Environment configuration
CACHE_RETRIES_DEFAULT = int(os.getenv("CACHE_RETRIES", "2"))
CACHE_DELAY_DEFAULT = int(os.getenv("CACHE_DELAY", "2"))
SKIP_CACHE_INIT_DEFAULT = os.getenv("SKIP_CACHE_INIT", "0") == "1"

# Minimum acceptable size for schema files in bytes
MIN_SCHEMA_FILE_SIZE = 4096  # 4 KB

# ANSI color codes
COLOR_YELLOW = "\033[33m"
COLOR_GREEN = "\033[32m"
COLOR_RED = "\033[31m"
COLOR_RESET = "\033[0m"

# List of files required for the application to run
REQUIRED_FILES: List[Path] = [
    Path("cache/schema/items.json"),
    Path("cache/schema/attributes.json"),
    Path("cache/schema/particles.json"),
    Path("cache/schema/effects.json"),
    Path("cache/schema/paints.json"),
    Path("cache/schema/parts.json"),
    Path("cache/schema/warpaints.json"),
    Path("cache/schema/qualities.json"),
    Path("cache/schema/defindexes.json"),
    Path("cache/schema/string_lookups.json"),
    Path("cache/prices.json"),
    Path("cache/currencies.json"),
]


async def _save_json_atomic(path: Path, data: object) -> None:
    """Write ``data`` to ``path`` atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


async def _download_schema_section(
    client,
    provider: SchemaProvider,
    key: str,
    endpoint: str,
    save_func=_save_json_atomic,
) -> None:
    data = await provider._fetch_async(client, endpoint)
    if isinstance(data, dict) and "value" in data:
        data = data["value"]
    if (
        key == "effects"
        and isinstance(data, dict)
        and not any(str(k).isdigit() for k in data)
        and all(str(v).isdigit() for v in data.values())
    ):
        data = {int(v): k for k, v in data.items()}
    path = provider._cache_file(key)
    await save_func(path, data)
    count = len(data) if hasattr(data, "__len__") else 0
    print(f"\N{CHECK MARK} Saved {path} ({count} entries)")


async def _refresh_schema_concurrent(save_func=_save_json_atomic) -> None:
    provider = SchemaProvider(cache_dir="cache/schema")
    async with __import__("httpx").AsyncClient() as client:
        tasks = [
            _download_schema_section(client, provider, k, ep, save_func)
            for k, ep in provider.ENDPOINTS.items()
        ]
        await asyncio.gather(*tasks)


async def _do_refresh() -> int:
    """Fetch all schema and price data in parallel and return count of schema files written."""
    print(
        "\N{ANTICLOCKWISE OPEN CIRCLE ARROW} Refreshing TF2 schema (full update)...",
        flush=True,
    )

    count = 0

    provider = SchemaProvider(cache_dir="cache/schema")
    for key in provider.ENDPOINTS:
        path = provider._cache_file(key)
        if path.exists():
            size = path.stat().st_size
            if size < MIN_SCHEMA_FILE_SIZE:
                print(
                    f"{COLOR_YELLOW}⚠ Detected incomplete schema cache ({size} bytes). Re-fetching...{COLOR_RESET}"
                )
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass

    async def counting_save(path: Path, data: object) -> None:
        nonlocal count
        await _save_json_atomic(path, data)
        count += 1

    await _refresh_schema_concurrent(save_func=counting_save)

    price_task = asyncio.create_task(ensure_prices_cached_async(refresh=True))
    curr_task = asyncio.create_task(ensure_currencies_cached_async(refresh=True))
    price_path, curr_path = await asyncio.gather(price_task, curr_task)

    if price_path.exists() and price_path.stat().st_size <= 2:
        print(f"{COLOR_YELLOW}⚠ Pricing unavailable (using empty cache).{COLOR_RESET}")
    else:
        print(f"\N{CHECK MARK} Saved {price_path}")
    print(f"\N{CHECK MARK} Saved {curr_path}")
    print(
        "\N{CHECK MARK} Refresh complete. Restart app normally without --refresh to start server.",
        flush=True,
    )

    return count


def missing_cache_files() -> List[Path]:
    """Return list of required cache files that are missing or incomplete."""
    return [
        p
        for p in REQUIRED_FILES
        if not p.exists() or p.stat().st_size < MIN_SCHEMA_FILE_SIZE
    ]


def validate_cache_files() -> bool:
    """Return ``True`` if all required files exist and are non-empty."""
    return not missing_cache_files()


async def fetch_missing_cache_files() -> bool:
    """Download any missing cache files with progress and retries."""

    if os.getenv("SKIP_CACHE_INIT", "1" if SKIP_CACHE_INIT_DEFAULT else "0") == "1":
        print(
            f"{COLOR_YELLOW}⚠ Cache validation skipped (SKIP_CACHE_INIT=1){COLOR_RESET}"
        )
        return True

    retries = int(os.getenv("CACHE_RETRIES", str(CACHE_RETRIES_DEFAULT)))
    delay = int(os.getenv("CACHE_DELAY", str(CACHE_DELAY_DEFAULT)))

    if retries > 1:
        print(
            f"{COLOR_YELLOW}Retrying up to {retries} times with {delay} sec delay between attempts{COLOR_RESET}"
        )

    missing_count = 0
    refreshed_count = 0

    for attempt in range(1, retries + 1):
        missing = missing_cache_files()
        if not missing:
            print(
                f"{COLOR_GREEN}✅ All schema files verified. Starting server.{COLOR_RESET}"
            )
            return True

        initial_missing = list(missing)
        if missing_count == 0:
            missing_count = len(initial_missing)
        total = len(initial_missing)
        for i, path in enumerate(initial_missing, 1):
            print(f"{COLOR_YELLOW}🟡 [{i}/{total}] Fetching {path}...{COLOR_RESET}")

        try:
            refreshed_count = await _do_refresh()
        except Exception as exc:  # pragma: no cover - network failures logged
            print(f"{COLOR_RED}❌ Refresh attempt {attempt} failed: {exc}{COLOR_RESET}")

        remaining = missing_cache_files()
        for i, path in enumerate(initial_missing, 1):
            if path not in remaining:
                print(
                    f"{COLOR_GREEN}✅ [{i}/{total}] {path} downloaded successfully{COLOR_RESET}"
                )

        if not remaining:
            total_updated = refreshed_count
            print(
                f"{COLOR_GREEN}✅ Cache verified. {missing_count} missing files downloaded. Full schema refresh updated {total_updated} files total, including prices and currencies.{COLOR_RESET}"
            )
            return True

        if attempt < retries:
            await asyncio.sleep(delay)

    final_missing = missing_cache_files()
    if final_missing:
        paths = ", ".join(map(str, final_missing))
        print(f"{COLOR_RED}❌ Failed after {retries} retries: {paths}{COLOR_RESET}")
        return False

    total_updated = refreshed_count
    print(
        f"{COLOR_GREEN}✅ Cache verified. {missing_count} missing files downloaded. Full schema refresh updated {total_updated} files total, including prices and currencies.{COLOR_RESET}"
    )
    return True


__all__ = [
    "REQUIRED_FILES",
    "missing_cache_files",
    "validate_cache_files",
    "fetch_missing_cache_files",
    "_do_refresh",
]
