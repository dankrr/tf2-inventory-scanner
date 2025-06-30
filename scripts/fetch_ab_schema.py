import json
import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

BASE = "https://schema.autobot.tf"
CACHE_DIR = Path("cache")

ENDPOINTS = {
    "/schema": "ab_schema.json",
    "/properties/qualities": "ab_qualities.json",
    "/properties/killstreaks": "ab_killstreaks.json",
    "/properties/effects": "ab_effects.json",
    "/properties/paintkits": "ab_paintkits.json",
    "/properties/paints": "ab_paints.json",
    "/properties/strangeParts": "ab_parts.json",
    "/properties/crateseries": "ab_crates.json",
    "/properties/craftWeapons": "ab_craft.json",
    "/properties/uncraftWeapons": "ab_craft.json",
    "/getItemObject/fromSkuBulk": "ab_bulk_item.json",
}


def _save(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f)


def fetch_all_ab_schema() -> None:
    """Fetch autobot schema endpoints and cache them."""
    for endpoint, fname in ENDPOINTS.items():
        url = f"{BASE}{endpoint}"
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            _save(CACHE_DIR / fname, data)
            count = len(data) if hasattr(data, "__len__") else 0
            logger.info("Fetched %s entries from %s", count, endpoint)
        except Exception as exc:  # pragma: no cover - network failure
            logger.error("Failed to fetch %s: %s", endpoint, exc)


__all__ = ["fetch_all_ab_schema"]
