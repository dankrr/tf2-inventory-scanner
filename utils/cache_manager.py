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

# Minimum acceptable size for cache files in bytes
MIN_SCHEMA_FILE_SIZE = 1024  # 1 KB
MIN_PRICES_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MIN_CURRENCIES_FILE_SIZE = 1024  # 1 KB

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

# Set of schema file names for quick category checks
SCHEMA_FILE_NAMES = {p.name for p in REQUIRED_FILES if "schema" in p.parts}


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

    price_path = Path("cache/prices.json")
    if price_path.exists():
        size = price_path.stat().st_size
        if size < MIN_PRICES_FILE_SIZE:
            print(
                f"{COLOR_YELLOW}⚠ Detected incomplete price cache ({size} bytes). Re-fetching...{COLOR_RESET}"
            )
            try:
                price_path.unlink()
            except FileNotFoundError:
                pass

    curr_path = Path("cache/currencies.json")
    if curr_path.exists():
        size = curr_path.stat().st_size
        if size < MIN_CURRENCIES_FILE_SIZE:
            print(
                f"{COLOR_YELLOW}⚠ Detected incomplete currency cache ({size} bytes). Re-fetching...{COLOR_RESET}"
            )
            try:
                curr_path.unlink()
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


def _size_threshold(path: Path) -> int:
    if path.name == "prices.json":
        return MIN_PRICES_FILE_SIZE
    if path.name == "currencies.json":
        return MIN_CURRENCIES_FILE_SIZE
    if path.name == "qualities.json":
        return 100
    return MIN_SCHEMA_FILE_SIZE


def missing_cache_files() -> List[Path]:
    """Return list of required cache files that are missing or incomplete."""
    return [
        p
        for p in REQUIRED_FILES
        if not p.exists() or p.stat().st_size < _size_threshold(p)
    ]


def validate_cache_files() -> bool:
    """Return ``True`` if all required files exist and are non-empty."""
    return not missing_cache_files()


async def fetch_missing_cache_files() -> tuple[bool, bool, bool]:
    """Download any missing cache files with progress and retries.

    Returns a tuple ``(ok, refreshed, schema_refreshed)`` where ``ok`` indicates
    whether all cache files are present after the operation, ``refreshed``
    reports whether any files were downloaded, and ``schema_refreshed`` is
    ``True`` only if a schema refresh occurred.  The latter allows callers to
    decide whether a restart is necessary.
    """

    if os.getenv("SKIP_CACHE_INIT", "1" if SKIP_CACHE_INIT_DEFAULT else "0") == "1":
        print(
            f"{COLOR_YELLOW}⚠ Cache validation skipped (SKIP_CACHE_INIT=1){COLOR_RESET}"
        )
        return True, False, False

    retries = int(os.getenv("CACHE_RETRIES", str(CACHE_RETRIES_DEFAULT)))
    delay = int(os.getenv("CACHE_DELAY", str(CACHE_DELAY_DEFAULT)))

    if retries > 1:
        print(
            f"{COLOR_YELLOW}Retrying up to {retries} times with {delay} sec delay between attempts{COLOR_RESET}"
        )

    missing_count = 0
    refreshed_any = False
    schema_refreshed = False
    price_refreshed = False
    currency_refreshed = False

    for attempt in range(1, retries + 1):
        missing = missing_cache_files()
        if not missing:
            if refreshed_any:
                summary = (
                    f"{COLOR_GREEN}✅ Cache ready: {missing_count} files refreshed ("
                    f"schema: {'yes' if schema_refreshed else 'no'}, "
                    f"pricing: {'yes' if price_refreshed else 'no'}, "
                    f"currencies: {'yes' if currency_refreshed else 'no'}){COLOR_RESET}"
                )
            else:
                summary = f"{COLOR_GREEN}✅ All cache files verified. No refresh needed.{COLOR_RESET}"
            print(summary)
            return True, refreshed_any, schema_refreshed

        initial_missing = list(missing)
        if missing_count == 0:
            missing_count = len(initial_missing)
        total = len(initial_missing)
        for i, path in enumerate(initial_missing, 1):
            print(f"{COLOR_YELLOW}🟡 [{i}/{total}] Fetching {path}...{COLOR_RESET}")

        try:
            if any(p.name in SCHEMA_FILE_NAMES for p in missing):
                await _refresh_schema_concurrent()
                schema_refreshed = True
                refreshed_any = True
            if any(p.name == "prices.json" for p in missing):
                await ensure_prices_cached_async(refresh=True)
                price_refreshed = True
                refreshed_any = True
            if any(p.name == "currencies.json" for p in missing):
                await ensure_currencies_cached_async(refresh=True)
                currency_refreshed = True
                refreshed_any = True
        except Exception as exc:  # pragma: no cover - network failures logged
            print(f"{COLOR_RED}❌ Refresh attempt {attempt} failed: {exc}{COLOR_RESET}")

        remaining = missing_cache_files()
        for i, path in enumerate(initial_missing, 1):
            if path not in remaining:
                print(
                    f"{COLOR_GREEN}✅ [{i}/{total}] {path} downloaded successfully{COLOR_RESET}"
                )

        if not remaining:
            summary = (
                f"{COLOR_GREEN}✅ Cache ready: {missing_count} files refreshed ("
                f"schema: {'yes' if schema_refreshed else 'no'}, "
                f"pricing: {'yes' if price_refreshed else 'no'}, "
                f"currencies: {'yes' if currency_refreshed else 'no'}){COLOR_RESET}"
            )
            print(summary)
            return True, refreshed_any, schema_refreshed

        if attempt < retries:
            await asyncio.sleep(delay)

    final_missing = missing_cache_files()
    if final_missing:
        paths = ", ".join(map(str, final_missing))
        print(f"{COLOR_RED}❌ Failed after {retries} retries: {paths}{COLOR_RESET}")
        return False, refreshed_any, schema_refreshed

    summary = (
        f"{COLOR_GREEN}✅ Cache ready: {missing_count} files refreshed ("
        f"schema: {'yes' if schema_refreshed else 'no'}, "
        f"pricing: {'yes' if price_refreshed else 'no'}, "
        f"currencies: {'yes' if currency_refreshed else 'no'}){COLOR_RESET}"
    )
    print(summary)
    return True, refreshed_any, schema_refreshed


__all__ = [
    "REQUIRED_FILES",
    "missing_cache_files",
    "validate_cache_files",
    "fetch_missing_cache_files",
    "_do_refresh",
]
