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
    """Fetch schema overview and all items from Steam."""

    overview_url = (
        "https://api.steampowered.com/IEconItems_440/GetSchemaOverview/v1/"
        f"?key={api_key}"
    )
    r = requests.get(overview_url, timeout=20)
    r.raise_for_status()
    overview = r.json()["result"]
    qualities = {str(v): k for k, v in overview.get("qualities", {}).items()}

    items: Dict[str, Any] = {}
    start = 0
    while True:
        items_url = (
            "https://api.steampowered.com/IEconItems_440/GetSchemaItems/v1/"
            f"?key={api_key}&start={start}"
        )
        r = requests.get(items_url, timeout=20)
        r.raise_for_status()
        data = r.json()["result"]
        for item in data.get("items", []):
            defindex = str(item.get("defindex"))
            if not defindex or "name" not in item:
                continue
            items[defindex] = {
                "defindex": item.get("defindex"),
                "name": item.get("name"),
                "image_url": item.get("image_url"),
                "image_url_large": item.get("image_url_large"),
            }
        if not data.get("next"):
            break
        start = data["next"]

    return {"items": items, "qualities": qualities}


def ensure_schema_cached(api_key: str | None = None) -> Dict[str, Any]:
    """Return cached item schema mapping."""
    if api_key is None:
        api_key = os.getenv("STEAM_API_KEY")

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
