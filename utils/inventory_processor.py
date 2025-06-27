from typing import Any, Dict, List, Tuple
from urllib.parse import quote
import logging

from . import steam_api_client, schema_fetcher

logger = logging.getLogger(__name__)


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
    schema_items = schema_fetcher.SCHEMA or {}
    qualities = schema_fetcher.QUALITIES or {}

    for entry in items_raw:
        defindex = str(entry.get("defindex"))
        schema_item = schema_items.get(defindex)
        if not schema_item:
            continue
        name = schema_item.get("name")
        icon_url = schema_item.get("image_url")
        image_url = (
            f"https://community.cloudflare.steamstatic.com/economy/image/{quote(icon_url, safe='')}"
            if icon_url
            else ""
        )
        quality_val = entry.get("quality")
        quality = qualities.get(str(quality_val), qualities.get(quality_val))
        items.append(
            {
                "defindex": defindex,
                "item_name": name,
                "quality": quality,
                "image_url": image_url,
                "attributes": entry.get("attributes", []),
            }
        )
    return items


def process_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Public wrapper that sorts items by name."""
    items = enrich_inventory(data)
    return sorted(items, key=lambda i: i["item_name"])
