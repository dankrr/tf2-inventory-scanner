"""Helpers for downloading and caching the TF2 item schema."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

# cache file location and refresh interval (1 day)
CACHE_FILE = Path("data/cached_schema.json")
TTL = 24 * 60 * 60

# remote schema endpoint
SCHEMA_URL = "https://schema.autobot.tf/schema/download"
BULK_NAME_URL = "https://schema.autobot.tf/getName/fromItemObjectBulk"


SCHEMA: Dict[str, Any] | None = None


def _fetch_schema() -> Dict[str, Any]:
    """Return the raw schema JSON payload from the remote endpoint."""

    last_exc: Exception | None = None
    for _ in range(3):
        try:
            r = requests.get(SCHEMA_URL, timeout=20)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:  # pragma: no cover - network
            last_exc = exc
            time.sleep(1)
    raise RuntimeError(f"Schema fetch failed: {last_exc}")


def _download_schema() -> Dict[str, Any]:
    """Download the raw TF2 schema and save it to the cache file."""

    logger.info("Fetching schema from %s", SCHEMA_URL)
    data = _fetch_schema()
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("Invalid schema format: missing 'items' list")
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_FILE.open("w") as f:
        json.dump(data, f)
    logger.info("Schema fetch success, saved to cache (%s items)", len(items))
    return data


def _load_schema() -> Dict[str, Any]:
    """Parse the cached schema file and build an item mapping."""

    try:
        with CACHE_FILE.open() as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to read schema cache: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Schema JSON is not an object")

    items_raw = data.get("items")
    if not isinstance(items_raw, list):
        raise ValueError("Schema 'items' not a list")

    logger.debug(
        "Schema items structure: type=%s count=%s",
        type(items_raw).__name__,
        len(items_raw) if isinstance(items_raw, list) else "N/A",
    )
    if isinstance(items_raw, list) and items_raw:
        logger.debug("First schema entry keys: %s", list(items_raw[0].keys()))

    items: Dict[str, Any] = {}
    for item in items_raw:
        defindex = item.get("defindex")
        if defindex is None:
            continue
        quality = item.get("quality", 0)
        craftable = item.get("craftable", True)
        key = f"{defindex};{quality};{1 if craftable else 0}"
        items[key] = item

    return items


def ensure_schema_cached() -> Dict[str, Any]:
    """Return cached item schema mapping."""

    global SCHEMA

    need_fetch = (
        not CACHE_FILE.exists() or time.time() - CACHE_FILE.stat().st_mtime > TTL
    )
    if need_fetch:
        try:
            _download_schema()
            source = "fetched"
        except Exception as exc:
            logger.warning("Schema fetch failed: %s", exc)
            if not CACHE_FILE.exists():
                raise RuntimeError("No schema cache available") from exc
            source = "cache"
            if time.time() - CACHE_FILE.stat().st_mtime > TTL:
                logger.warning("Using stale schema cache")
    else:
        source = "cache"

    try:
        SCHEMA = _load_schema()
    except Exception as exc:  # pragma: no cover - config error
        raise RuntimeError(f"Failed to load schema: {exc}") from exc

    if not SCHEMA:
        raise RuntimeError("Schema cache empty")

    logger.info("Loaded %s schema items from %s", len(SCHEMA), source)
    return SCHEMA


def resolve_item_names_bulk(objs: list[dict]) -> list[str]:
    """Return display names for a list of item objects."""

    r = requests.post(
        BULK_NAME_URL,
        headers={"Content-Type": "application/json"},
        json=objs,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("itemNames", [])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TF2 schema cache helper")
    parser.add_argument(
        "--show",
        action="store_true",
        help="Load schema and print a brief summary",
    )
    args = parser.parse_args()
    ensure_schema_cached()
    if args.show:
        if SCHEMA:
            first = next(iter(SCHEMA.values()))
            print(f"Total items: {len(SCHEMA)}")
            print(f"First item keys: {list(first.keys())}")
        else:
            print("Schema not loaded")
