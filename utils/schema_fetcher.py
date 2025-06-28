import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

# cache file location and refresh interval
CACHE_FILE = Path("data/cached_schema.json")
TTL = 48 * 60 * 60  # 48 hours

# remote schema endpoint
SCHEMA_URL = "https://schema.autobot.tf/schema/download"
BULK_NAME_URL = "https://schema.autobot.tf/getName/fromItemObjectBulk"


SCHEMA: Dict[str, Any] | None = None


def _download_schema() -> None:
    """Download the raw TF2 schema and save it to the cache file."""

    logger.info("Fetching schema from %s", SCHEMA_URL)
    r = requests.get(SCHEMA_URL, stream=True, timeout=20)
    r.raise_for_status()
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_FILE.open("wb") as f:
        f.write(r.content)
    logger.info("Schema fetch success, saved to cache")


def _load_schema() -> Dict[str, Any]:
    """Parse the cached schema file and build an item mapping."""

    with CACHE_FILE.open() as f:
        data = json.load(f)

    logger.debug("Schema cache loaded: type=%s", type(data).__name__)

    if not isinstance(data, dict):
        logger.error("Schema cache not an object; type=%s", type(data).__name__)
        return {}

    items_raw = data.get("items", [])
    if not isinstance(items_raw, list):
        logger.error("Schema 'items' not a list; type=%s", type(items_raw).__name__)
        return {}

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

    refresh = not CACHE_FILE.exists() or time.time() - CACHE_FILE.stat().st_mtime > TTL
    if refresh:
        _download_schema()
        logger.info("Schema cache updated at %s", CACHE_FILE)
    else:
        logger.info("Schema cache is still fresh")

    SCHEMA = _load_schema()
    logger.info("Loaded %s schema items", len(SCHEMA))
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
