import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict

import requests

CLOUD = "https://steamcommunity-a.akamaihd.net/economy/image/"

logger = logging.getLogger(__name__)

CACHE_FILE = Path("cache/tf2_schema.json")
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

            path = (
                item.get("image_url_large")
                or item.get("image_url")
                or item.get("icon_url_large")
                or item.get("icon_url")
                or ""
            )
            if path.startswith("http"):
                image_url = path
            elif path:
                image_url = f"{CLOUD}{path}/360fx360f"
            else:
                image_url = ""

            items[defindex] = {
                "defindex": item.get("defindex"),
                "name": item.get("name"),
                "image_url": image_url,
            }
        if not data.get("next"):
            break
        start = data["next"]

    return {"items": items, "qualities": qualities}


def ensure_schema_cached(api_key: str | None = None) -> Dict[str, Any]:
    """Return cached item schema mapping, refetching if missing or stale."""

    if api_key is None:
        api_key = os.getenv("STEAM_API_KEY")

    global SCHEMA, QUALITIES
    cache_path = CACHE_FILE.resolve()
    need_fetch = True
    if cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age < TTL:
            with cache_path.open() as f:
                cached = json.load(f)
            items = cached.get("items", cached)
            if isinstance(items, dict) and len(items) >= 5000:
                SCHEMA = items
                QUALITIES = cached.get("qualities", {})
                logger.info("Loaded %s items from %s", len(SCHEMA), cache_path)
                need_fetch = False

    if need_fetch:
        logger.warning("\N{CROSS MARK} Schema missing or invalid — refetching...")
        fetched = _fetch_schema(api_key)
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(fetched))
        SCHEMA = fetched["items"]
        QUALITIES = fetched["qualities"]
        logger.info(
            "\N{CHECK MARK} Fetched and cached full schema with %s items → %s",
            len(SCHEMA),
            cache_path,
        )

    return SCHEMA


def refresh_schema(api_key: str | None = None) -> Dict[str, Any]:
    """Force download of the latest schema and update the cache."""

    if api_key is None:
        api_key = os.getenv("STEAM_API_KEY")

    fetched = _fetch_schema(api_key)
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(fetched))
    global SCHEMA, QUALITIES
    SCHEMA = fetched["items"]
    QUALITIES = fetched.get("qualities", {})
    logger.info(
        "\N{CHECK MARK} Fetched and cached full schema with %s items → %s",
        len(SCHEMA),
        CACHE_FILE,
    )
    return SCHEMA
