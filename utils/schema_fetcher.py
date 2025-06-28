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


def _fetch_schema() -> Dict[str, Any]:
    """Fetch enriched TF2 schema from schema.autobot.tf."""

    logger.info("Fetching schema from %s", SCHEMA_URL)
    r = requests.get(SCHEMA_URL, headers={"Accept": "*/*"})
    r.raise_for_status()
    data = r.json()
    logger.info("Fetched schema with %s items", len(data.get("items", [])))
    return data


def ensure_schema_cached() -> Dict[str, Any]:
    """Return cached item schema mapping."""

    global SCHEMA
    if CACHE_FILE.exists():
        logger.info("Loading schema from cache %s", CACHE_FILE)
        with CACHE_FILE.open() as f:
            cached = json.load(f)
        ts = cached.get("timestamp", 0)
        if time.time() - ts < TTL:
            SCHEMA = cached.get("items", {})
            logger.info("Schema cache HIT: %s items", len(SCHEMA))
            return SCHEMA

    fetched = _fetch_schema()
    items: Dict[str, Any] = {}
    for item in fetched.get("items", []):
        defindex = item.get("defindex")
        if defindex is None:
            continue
        quality = item.get("quality", 0)
        craftable = item.get("craftable", True)
        key = f"{defindex};{quality};{1 if craftable else 0}"
        items[key] = item

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_FILE.open("w") as f:
        json.dump({"timestamp": time.time(), "items": items}, f)
    SCHEMA = items
    logger.info("Schema cache MISS, fetched %s items", len(SCHEMA))
    logger.info("Schema cache updated at %s", CACHE_FILE)
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
