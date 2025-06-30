import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

BASE = "https://schema.autobot.tf"
CACHE_PATH = Path("cache/tf2_schema.json")
TTL = 48 * 60 * 60  # 48 hours

SCHEMA: Dict[str, Any] | None = None


def _fetch_schema() -> Dict[str, Any]:
    """Fetch TF2 schema data from AutoBot."""
    resp = requests.get(f"{BASE}/schema", timeout=20)
    resp.raise_for_status()
    return resp.json()


def ensure_schema_cached() -> Dict[str, Any]:
    """Return cached TF2 schema, fetching if necessary."""
    global SCHEMA

    if CACHE_PATH.exists():
        age = time.time() - CACHE_PATH.stat().st_mtime
        if age < TTL:
            with CACHE_PATH.open() as fh:
                SCHEMA = json.load(fh)
            logger.info("TF2 schema cache HIT: %s keys", len(SCHEMA))
            return SCHEMA

    data = _fetch_schema()
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("w") as fh:
        json.dump(data, fh)
    SCHEMA = data
    logger.info("TF2 schema cache MISS, fetched %s keys", len(SCHEMA))
    return SCHEMA


__all__ = ["ensure_schema_cached"]
