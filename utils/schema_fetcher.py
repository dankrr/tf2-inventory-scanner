import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

CACHE_FILE = Path("data/item_schema.json")
TTL = 48 * 60 * 60  # 48 hours


SCHEMA: Dict[str, Any] | None = None
QUALITIES: Dict[str | int, str] = {}


def _fetch_schema(api_key: str) -> Dict[str, Any]:
    """Fetch the full TF2 item schema in one request."""

    url = (
        "https://api.steampowered.com/IEconItems_440/GetSchema/v0001/" f"?key={api_key}"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()["result"]
    qualities = {str(v): k for k, v in data.get("qualities", {}).items()}

    items: Dict[str, Any] = {}
    for item in data.get("items", []):
        defindex = str(item.get("defindex"))
        if not defindex:
            continue
        if "name" not in item and "item_name" not in item:
            continue
        items[defindex] = {
            "defindex": item.get("defindex"),
            "name": item.get("name"),
            "item_name": item.get("item_name"),
            "image_url": item.get("image_url"),
            "image_url_large": item.get("image_url_large"),
        }

    return {"items": items, "qualities": qualities}


def ensure_schema_cached(api_key: str | None = None) -> Dict[str, Any]:
    """Return cached item schema mapping."""
    if api_key is None:
        api_key = os.getenv("STEAM_API_KEY")
    if not api_key:
        raise ValueError("STEAM_API_KEY is required to fetch item schema")

    global SCHEMA, QUALITIES
    if CACHE_FILE.exists():
        age = time.time() - CACHE_FILE.stat().st_mtime
        if age < TTL:
            with CACHE_FILE.open() as f:
                cached = json.load(f)
            SCHEMA = cached.get("items", {})
            QUALITIES = cached.get("qualities", {})
            logger.info("Schema cache HIT: %s items", len(SCHEMA))
            return SCHEMA

    fetched = _fetch_schema(api_key)
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_FILE.open("w") as f:
        json.dump(fetched, f)
    SCHEMA = fetched["items"]
    QUALITIES = fetched["qualities"]
    logger.info("Schema cache MISS, fetched %s items", len(SCHEMA))
    return SCHEMA
