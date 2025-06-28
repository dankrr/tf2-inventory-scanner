from typing import Any, Dict, List, Tuple
import logging
import re
from html import unescape

import json
from pathlib import Path

from . import steam_api_client, schema_fetcher, items_game_cache, local_data

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


def _extract_unusual_effect(asset: Dict[str, Any]) -> str | None:
    """Return the unusual effect name from attributes or descriptions."""

    if "effect" in asset:
        name = local_data.EFFECT_NAMES.get(str(asset["effect"]))
        if name:
            return name

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx == 134:
            val = str(int(attr.get("float_value", 0)))
            name = local_data.EFFECT_NAMES.get(val)
            if name:
                return name

    for desc in asset.get("descriptions", []):
        if not isinstance(desc, dict):
            continue
        text = unescape(desc.get("value", ""))
        text = re.sub(r"<[^>]+>", "", text)
        match = re.search(r"Unusual Effect:\s*(.+)", text, re.I)
        if match:
            return match.group(1).strip()
    return None


def _build_item_name(base: str, quality: str, asset: Dict[str, Any]) -> str:
    """Return the display name prefixed with quality/effect."""

    parts: List[str] = []
    effect = _extract_unusual_effect(asset)
    if effect:
        parts.append(effect)
        if quality not in ("Unique", "Normal", "Unusual"):
            parts.append(quality)
    else:
        if quality not in ("Unique", "Normal"):
            parts.append(quality)
    parts.append(base)
    return " ".join(parts)


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
    schema_map = local_data.TF2_SCHEMA or schema_fetcher.SCHEMA or {}
    cleaned_map = local_data.ITEMS_GAME_CLEANED or items_game_cache.ITEM_BY_DEFINDEX

    for asset in items_raw:
        defindex = str(asset.get("defindex", "0"))
        entry = cleaned_map.get(defindex) or schema_map.get(defindex)
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

        # Prefer name from cleaned items_game if available
        ig_item = cleaned_map.get(defindex) or {}
        base_name = (
            WARPAINT_MAP.get(defindex)
            or ig_item.get("name")
            or entry.get("item_name")
            or entry.get("name")
            or f"Item #{defindex}"
        )

        quality_id = asset.get("quality", 0)
        q_name, q_col = QUALITY_MAP.get(quality_id, ("Unknown", "#B2B2B2"))
        display_name = _build_item_name(base_name, q_name, asset)

        item = {
            "defindex": defindex,
            "name": display_name,
            "quality": q_name,
            "quality_color": q_col,
            "image_url": image_path,
            "final_url": final_url,
        }
        items.append(item)

        if len(items) <= 3:
            effect_id = asset.get("effect")
            ks = None
            sheen = None
            for attr in asset.get("attributes", []):
                idx = attr.get("defindex")
                val = int(attr.get("float_value", 0))
                if idx == 2025:
                    ks = val
                elif idx == 2014:
                    sheen = val
                elif idx == 134 and effect_id is None:
                    effect_id = val
            print(
                f"Parsed: {display_name} (defindex {defindex}, effect: {effect_id}, ks: {ks}, sheen: {sheen})"
            )
    return items


def process_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Public wrapper that sorts items by name."""
    items = enrich_inventory(data)
    return sorted(items, key=lambda i: i["name"])
