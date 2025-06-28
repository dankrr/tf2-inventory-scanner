from typing import Any, Dict, List, Tuple
import logging

from . import steam_api_client, schema_fetcher

logger = logging.getLogger(__name__)

# Base URL for item images
CLOUD = "https://steamcommunity.cloudflare.steamstatic.com/economy/image/"

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

        image_path = entry.get("image_url") or ""
        if image_path.startswith("http"):
            final_url = image_path
        else:
            final_url = f"{CLOUD}{image_path}" if image_path else ""

        name = (
            asset.get("market_hash_name")
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
                "quality_id": quality_id,
                "image_url": image_path,
                "final_url": final_url,
                "uncraftable": bool(asset.get("flag_cannot_craft")),
                "australium": bool(asset.get("australium")),
                "tradable": not asset.get("flag_cannot_trade", False),
                "effect": asset.get("quality2"),
            }
        )
    return items


def process_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Public wrapper that sorts items by name."""
    items = enrich_inventory(data)
    return sorted(items, key=lambda i: i["name"])
