from typing import Any, Dict, List, Tuple
import logging

import json
from pathlib import Path

from . import steam_api_client, schema_fetcher

logger = logging.getLogger(__name__)

# Base URL for item images
CLOUD = "https://steamcommunity-a.akamaihd.net/economy/image/"

# Mapping of defindex -> human readable name for warpaints
MAPPING_FILE = Path(__file__).with_name("warpaint_mapping.json")
WARPAINT_MAP: Dict[str, str] = {}
if MAPPING_FILE.exists():
    with MAPPING_FILE.open() as f:
        WARPAINT_MAP = json.load(f)

# Map of quality ID to (name, background color)
QUALITY_MAP = {
    0: ("Normal", "#B2B2B2"),
    1: ("Genuine", "#4D7455"),
    3: ("Vintage", "#476291"),
    5: ("Unusual", "#8650AC"),
    6: ("Unique", "#FFD700"),
    11: ("Strange", "#CF6A32"),
    13: ("Haunted", "#38F3AB"),
}


def fetch_inventory(steamid: str) -> Tuple[Dict[str, Any], str]:
    """Return inventory data and status using the Steam API helper."""

    status, data = steam_api_client.fetch_inventory(steamid)
    if status not in ("parsed", "incomplete"):
        data = {"items": []}
    else:
        data = data or {"items": []}
    return data, status


def enrich_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a list of inventory items enriched with schema info."""
    items_raw = data.get("items")
    if not isinstance(items_raw, list):
        return []

    items: List[Dict[str, Any]] = []
    schema_map = schema_fetcher.SCHEMA or {}

    for asset in items_raw:
        defindex = str(asset.get("defindex", "0"))
        entry = schema_map.get(defindex)
        if not entry:
            continue

        icon_url = asset.get("icon_url") or asset.get("icon_url_large")
        if icon_url:
            image_path = icon_url
            if icon_url.startswith("//"):
                final_url = "https:" + icon_url
            elif icon_url.startswith("http"):
                final_url = icon_url
            else:
                final_url = f"{CLOUD}{icon_url}/360fx360f"
        else:
            image_path = entry.get("image_url") or entry.get("image_url_large") or ""
            if image_path.startswith("http"):
                final_url = image_path
            else:
                final_url = f"{CLOUD}{image_path}" if image_path else ""

        name = (
            WARPAINT_MAP.get(defindex)
            or entry.get("item_name")
            or entry.get("name")
            or f"Item #{defindex}"
        )

        quality_id = asset.get("quality", 0)
        q_name, q_col = QUALITY_MAP.get(quality_id, ("Unknown", "#B2B2B2"))

        items.append(
            {
                "defindex": defindex,
                "name": name,
                "quality": q_name,
                "quality_color": q_col,
                "image_url": image_path,
                "final_url": final_url,
            }
        )
    return items


def process_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Public wrapper that sorts items by name."""
    items = enrich_inventory(data)
    return sorted(items, key=lambda i: i["name"])
