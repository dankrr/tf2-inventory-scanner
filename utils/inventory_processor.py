from typing import Any, Dict, List
from urllib.parse import quote

from .schema_fetcher import SCHEMA


def enrich_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a list of inventory items enriched with schema info."""
    desc_map = {d.get("classid"): d for d in data.get("descriptions", [])}
    items: List[Dict[str, Any]] = []
    for asset in data.get("assets", []):
        desc = desc_map.get(asset.get("classid"))
        if not desc:
            continue
        defindex = str(
            desc.get("app_data", {}).get("def_index") or desc.get("defindex")
        )
        schema_item = SCHEMA.get(defindex)
        if not schema_item:
            continue
        name = schema_item["name"]
        icon_url = desc.get("icon_url")
        image_url = (
            f"https://community.cloudflare.steamstatic.com/economy/image/{quote(icon_url, safe='')}"
            if icon_url
            else ""
        )
        quality = asset.get("quality")
        items.append(
            {
                "defindex": defindex,
                "name": name,
                "quality": quality,
                "image_url": image_url,
            }
        )
    return items


def process_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Public wrapper that sorts items by name."""
    items = enrich_inventory(data)
    return sorted(items, key=lambda i: i["name"])
