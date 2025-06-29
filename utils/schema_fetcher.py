import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict

import requests

CLOUD = "https://steamcommunity-a.akamaihd.net/economy/image/"
BASE_URL = "https://schema.autobot.tf"

logger = logging.getLogger(__name__)

CACHE_FILE = Path("cache/tf2schema.json")
TTL = 48 * 60 * 60  # 48 hours


SCHEMA: Dict[str, Any] | None = None
QUALITIES: Dict[str | int, str] = {}


def _fetch_schema(_: str | None = None) -> Dict[str, Any]:
    """Download the complete schema JSON from schema.autobot.tf."""

    url = f"{BASE_URL}/schema"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def ensure_schema_cached(api_key: str | None = None) -> Dict[str, Any]:
    """Return cached item schema mapping, refetching if missing or stale."""

    # The API key is ignored for Autobot but kept for backward compatibility.
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
