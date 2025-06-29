from __future__ import annotations

import json
import logging
import re
from html import unescape
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

from utils.local_data import *  # noqa: F401,F403
from . import items_game_cache, schema_fetcher, steam_api_client, local_data

logger = logging.getLogger(__name__)


# Mapping of defindex -> human readable name for warpaints
MAPPING_FILE = Path(__file__).with_name("warpaint_mapping.json")
WARPAINT_MAP: Dict[str, str] = {}
if MAPPING_FILE.exists():
    with MAPPING_FILE.open() as f:
        WARPAINT_MAP = json.load(f)


# Lookup tables come from utils.local_data via star import above.  Attribute
# handlers will be populated in later steps.

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

# Map of item origin ID -> human readable string
ORIGIN_MAP = {
    0: "Timed Drop",
    1: "Achievement",
    2: "Purchased",
    3: "Traded",
    4: "Crafted",
    5: "Store Promotion",
    6: "Gifted",
    7: "Support Promotion",
    8: "Found in Crate",
    9: "Earned",
    10: "Third-Party Promotion",
    11: "Purchased",
    12: "Halloween Drop",
    13: "Package Item",
    14: "Store Promotion",
    15: "Foreign",
}

ATTRIBUTE_HANDLERS: Dict[int, Callable[[Dict[str, Any], Dict[str, Any]], None]] = {}


def _attr_value(attr: Dict[str, Any]) -> Any:
    """Return generic attribute value supporting float_value or value."""

    if "value" in attr:
        return attr["value"]
    if "float_value" in attr:
        return attr["float_value"]
    return None


def handle_custom_name(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    val = _attr_value(attr)
    if val and not item.get("custom_name"):
        item["custom_name"] = str(val)


def handle_paint_color(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    val = _attr_value(attr)
    try:
        pid = int(val)
    except (TypeError, ValueError):
        return
    paint = local_data.PAINTS.get(pid)
    if not paint:
        return
    if not item.get("paint_name"):
        item["paint_name"] = paint["name"]
        item["paint_hex"] = paint["hex"]


def handle_spell_bitmask(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    val = _attr_value(attr)
    try:
        mask = int(val)
    except (TypeError, ValueError):
        return
    if not item.get("spell_flags"):
        item["spell_flags"] = {
            flag: False for _, flag in local_data.SPELL_BITFLAGS.values()
        }
    if "spells" not in item:
        item["spells"] = []
    for bit, (name, key) in local_data.SPELL_BITFLAGS.items():
        if mask & bit:
            item["spell_flags"][key] = True
            if name not in item["spells"]:
                item["spells"].append(name)
        else:
            item["spell_flags"].setdefault(key, False)


_TIER_LEVEL = {v: k for k, v in local_data.KILLSTREAK_TIERS.items()}


def handle_killstreak_tier(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    val = _attr_value(attr)
    try:
        level = int(val)
    except (TypeError, ValueError):
        return
    name = local_data.KILLSTREAK_TIERS.get(level)
    if not name:
        return
    existing = item.get("killstreak_tier")
    if not existing or level > _TIER_LEVEL.get(existing, 0):
        item["killstreak_tier"] = name


def handle_sheen(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    val = _attr_value(attr)
    try:
        idx = int(val)
    except (TypeError, ValueError):
        return
    name = local_data.SHEENS.get(idx)
    if name and not item.get("sheen"):
        item["sheen"] = name


def handle_killstreaker(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    val = _attr_value(attr)
    try:
        idx = int(val)
    except (TypeError, ValueError):
        return
    name = local_data.KILLSTREAKERS.get(idx) or local_data.EFFECT_NAMES.get(str(idx))
    if name and not item.get("killstreaker"):
        item["killstreaker"] = name


def handle_strange_part(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    name = local_data.STRANGE_PARTS.get(int(attr.get("defindex", 0)))
    if name and name not in item.get("strange_parts", []):
        item.setdefault("strange_parts", []).append(name)


def handle_festivized(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    val = _attr_value(attr)
    try:
        flag = int(val)
    except (TypeError, ValueError):
        flag = 0
    if flag:
        item["is_festivized"] = True


def handle_unusual_effect(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    val = _attr_value(attr)
    try:
        idx = int(val)
    except (TypeError, ValueError):
        return
    name = local_data.EFFECTS.get(idx) or local_data.EFFECT_NAMES.get(str(idx))
    if name and not item.get("unusual_effect"):
        item["unusual_effect"] = name


ATTRIBUTE_HANDLERS = {
    134: handle_custom_name,
    142: handle_paint_color,
    730: handle_spell_bitmask,
    2025: handle_killstreak_tier,
    2013: handle_sheen,
    2071: handle_killstreaker,
    380: handle_strange_part,
    381: handle_strange_part,
    382: handle_strange_part,
    383: handle_strange_part,
    384: handle_strange_part,
    385: handle_strange_part,
    2041: handle_festivized,
    2042: handle_festivized,
    2043: handle_festivized,
    2044: handle_festivized,
    214: handle_unusual_effect,
}


def _decode_attributes(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Return a dictionary of decoded attribute values."""

    result: Dict[str, Any] = {
        "strange_parts": [],
        "spells": [],
        "spell_flags": {},
        "misc_attrs": [],
        "is_festivized": False,
    }

    for attr in asset.get("attributes", []):
        idx = int(attr.get("defindex", 0))
        handler = ATTRIBUTE_HANDLERS.get(idx)
        if handler:
            handler(result, attr)
        else:
            result["misc_attrs"].append(attr)

    return result


def parse_spell_descriptions(
    asset: Dict[str, Any]
) -> Tuple[List[str], Dict[str, bool]]:
    lines: List[str] = []
    flags = {flag: False for _, flag in local_data.SPELL_BITFLAGS.values()}
    for desc in asset.get("descriptions", []):
        if not isinstance(desc, dict):
            continue
        text = re.sub(r"<[^>]+>", "", unescape(desc.get("value", ""))).strip()
        ltext = text.lower()
        if "halloween" in ltext or "spell" in ltext:
            lines.append(text)
        if "exorcism" in ltext:
            flags["exorcism"] = True
        if "paint" in ltext and "spell" in ltext:
            flags["paint_spell"] = True
        if "footprints" in ltext:
            flags["footprints"] = True
        if "pumpkin" in ltext:
            flags["pumpkin"] = True
        if "voices" in ltext or "rare spell" in ltext:
            flags["voices"] = True
    return lines, flags


def build_display_name(item: Dict[str, Any]) -> str:
    parts: List[str] = []
    if item.get("killstreak_tier"):
        parts.append(item["killstreak_tier"])
    if item.get("unusual_effect"):
        parts.append(item["unusual_effect"])
    if item.get("quality") not in ("Unique", "Normal"):
        if not (item.get("unusual_effect") and item["quality"] == "Unusual"):
            parts.append(item["quality"])
    parts.append(item.get("base_name", ""))
    if item.get("sheen"):
        parts.append(f"({item['sheen']})")
    return " ".join(p for p in parts if p)


def generate_badges(item: Dict[str, Any]) -> List[Dict[str, str]]:
    badges: List[Dict[str, str]] = []
    if item.get("paint_name"):
        badges.append({"icon": "🎨", "title": f"Painted: {item['paint_name']}"})
    if item.get("killstreak_tier"):
        badges.append({"icon": "⚔️", "title": item["killstreak_tier"]})
    if item.get("killstreaker"):
        badges.append({"icon": "💀", "title": f"Killstreaker: {item['killstreaker']}"})
    if item.get("sheen"):
        badges.append({"icon": "✨", "title": f"Sheen: {item['sheen']}"})
    flags = item.get("spell_flags", {})
    if flags.get("footprints"):
        badges.append({"icon": "👣", "title": "Fire Footprints"})
    if flags.get("exorcism"):
        badges.append({"icon": "👻", "title": "Exorcism"})
    if flags.get("pumpkin"):
        badges.append({"icon": "🎃", "title": "Pumpkin Bombs"})
    if flags.get("voices"):
        badges.append({"icon": "🗣", "title": "Voices From Below"})
    if item.get("strange_parts"):
        badges.append({"icon": "📊", "title": "Strange Parts"})
    if item.get("is_festivized"):
        badges.append({"icon": "🎄", "title": "Festivized"})
    if item.get("unusual_effect"):
        badges.append({"icon": "🔥", "title": f"Unusual: {item['unusual_effect']}"})
    return badges


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
        schema_entry = schema_map.get(defindex)
        ig_item = cleaned_map.get(defindex) or {}
        if not (schema_entry or ig_item):
            continue

        attr_data = _decode_attributes(asset)

        if not attr_data.get("spells"):
            lines, flags = parse_spell_descriptions(asset)
            if lines:
                attr_data["spells"] = lines
            if flags:
                attr_data["spell_flags"].update(flags)

        if not attr_data.get("unusual_effect"):
            effect_id = asset.get("effect")
            if effect_id:
                name = local_data.EFFECT_NAMES.get(str(effect_id))
                if name:
                    attr_data["unusual_effect"] = name
        if not attr_data.get("unusual_effect"):
            for desc in asset.get("descriptions", []):
                if not isinstance(desc, dict):
                    continue
                text = re.sub(r"<[^>]+>", "", unescape(desc.get("value", "")))
                m = re.search(r"Unusual Effect:\s*(.+)", text, re.I)
                if m:
                    attr_data["unusual_effect"] = m.group(1).strip()
                    break

        base_name = (
            WARPAINT_MAP.get(defindex)
            or ig_item.get("name")
            or (schema_entry.get("item_name") if schema_entry else None)
            or (schema_entry.get("name") if schema_entry else None)
            or f"Item #{defindex}"
        )

        if attr_data.get("custom_name"):
            base_name = f"{attr_data['custom_name']} | {base_name}"

        quality_id = asset.get("quality", 0)
        q_name, q_col = QUALITY_MAP.get(quality_id, ("Unknown", "#B2B2B2"))

        item: Dict[str, Any] = {
            "defindex": int(defindex),
            "base_name": base_name,
            "quality": q_name,
            "quality_color": q_col,
            "image_url": schema_entry.get("image_url") if schema_entry else "",
            "level": asset.get("level"),
            "origin": ORIGIN_MAP.get(asset.get("origin")),
        }

        item.update(attr_data)

        item["name"] = build_display_name(item)

        badges = generate_badges(item)
        if badges:
            item["badges"] = badges

        items.append(item)

    return items


def process_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Public wrapper that sorts items by name."""

    items = enrich_inventory(data)
    return sorted(items, key=lambda i: i["name"])
