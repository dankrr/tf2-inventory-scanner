from __future__ import annotations

# ruff: noqa: F401, F403, F405

import logging
import re
from html import unescape
from pathlib import Path
import json
from typing import Any, Callable, Dict, List, Tuple

from utils.local_data import *  # noqa: F401,F403,F405
import utils.local_data as ld
from . import items_game_cache, schema_fetcher, steam_api_client

logger = logging.getLogger(__name__)


# Mapping of defindex -> human readable name for warpaints
MAPPING_FILE = Path(__file__).with_name("warpaint_mapping.json")
WARPAINT_MAP: Dict[str, str] = {}
if MAPPING_FILE.exists():
    with MAPPING_FILE.open() as f:
        WARPAINT_MAP = json.load(f)


def handle_custom_name(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    val = attr.get("value") or attr.get("float_value")
    if isinstance(val, str) and val:
        if not item.get("custom_name"):
            item["custom_name"] = val


def handle_paint_color(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    value = (
        attr.get("value") if attr.get("value") is not None else attr.get("float_value")
    )
    if value is None:
        return
    try:
        pid = int(value)
    except (ValueError, TypeError):
        return
    paint = PAINTS.get(pid)
    if paint and not item.get("paint_name"):
        item["paint_name"] = paint.get("name")
        item["paint_hex"] = paint.get("hex")


SPELL_FLAG_SLUGS = {
    1: "footprints",
    2: "voices",
    4: "pumpkin",
    8: "exorcism",
    16: "paint_spell",
}


def handle_spell_bitmask(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    value = (
        attr.get("value") if attr.get("value") is not None else attr.get("float_value")
    )
    try:
        mask = int(value)
    except (ValueError, TypeError):
        mask = 0
    flags = {slug: bool(mask & bit) for bit, slug in SPELL_FLAG_SLUGS.items()}
    item["spell_flags"].update(flags)
    item.setdefault("spells", [])
    for bit in SPELL_FLAG_SLUGS:
        if mask & bit:
            name = SPELL_FLAGS.get(bit)
            if name and name not in item["spells"]:
                item["spells"].append(name)


KILLSTREAK_TIERS = {
    1: "Killstreak",
    2: "Specialized Killstreak",
    3: "Professional Killstreak",
}


def handle_killstreak_tier(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    value = (
        attr.get("value") if attr.get("value") is not None else attr.get("float_value")
    )
    try:
        tier_num = int(value)
    except (ValueError, TypeError):
        return
    tier = KILLSTREAK_TIERS.get(tier_num)
    if tier and not item.get("killstreak_tier"):
        item["killstreak_tier"] = tier


def handle_sheen(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    value = (
        attr.get("value") if attr.get("value") is not None else attr.get("float_value")
    )
    try:
        idx = int(value)
    except (ValueError, TypeError):
        return
    sheen = SHEENS.get(idx)
    if sheen and not item.get("sheen"):
        item["sheen"] = sheen


def handle_killstreaker(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    value = (
        attr.get("value") if attr.get("value") is not None else attr.get("float_value")
    )
    try:
        effect_id = int(value)
    except (ValueError, TypeError):
        return
    name = KILLSTREAKERS.get(effect_id)
    if name and not item.get("killstreaker"):
        item["killstreaker"] = name


def handle_strange_part(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    name = STRANGE_PARTS.get(int(attr.get("defindex", 0)))
    if name:
        parts = item.setdefault("strange_parts", [])
        if name not in parts:
            parts.append(name)


def handle_festivized(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    item["is_festivized"] = True


def handle_unusual_effect(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    value = (
        attr.get("value") if attr.get("value") is not None else attr.get("float_value")
    )
    try:
        effect_id = int(value)
    except (ValueError, TypeError):
        return
    name = EFFECTS.get(effect_id)
    if name and not item.get("unusual_effect"):
        item["unusual_effect"] = name


ATTRIBUTE_HANDLERS: Dict[int, Callable[[Dict[str, Any], Dict[str, Any]], None]] = {
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
    item: Dict[str, Any] = {
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
            handler(item, attr)
        else:
            item["misc_attrs"].append(attr)

    badges: List[Dict[str, str]] = []
    if item.get("paint_name"):
        badges.append({"icon": "🎨", "title": f"Painted: {item['paint_name']}"})
    if item.get("killstreak_tier"):
        badges.append({"icon": "⚔️", "title": item["killstreak_tier"]})
    if item.get("killstreaker"):
        badges.append({"icon": "💀", "title": f"Killstreaker: {item['killstreaker']}"})
    if item.get("sheen"):
        badges.append({"icon": "✨", "title": f"Sheen: {item['sheen']}"})
    spell_map = {
        "footprints": ("👣", "Fire Footprints"),
        "exorcism": ("👻", "Exorcism"),
        "pumpkin": ("🎃", "Pumpkin Bombs"),
        "voices": ("🗣", "Voices From Below"),
        "paint_spell": ("🎨", "Paint Spell"),
    }
    for key in ["footprints", "exorcism", "pumpkin", "voices", "paint_spell"]:
        if item.get("spell_flags", {}).get(key):
            icon, title = spell_map[key]
            badges.append({"icon": icon, "title": title})
    if item.get("strange_parts"):
        badges.append({"icon": "📊", "title": "Strange Parts"})
    if item.get("is_festivized"):
        badges.append({"icon": "🎄", "title": "Festivized"})
    if item.get("unusual_effect"):
        badges.append({"icon": "🔥", "title": f"Unusual: {item['unusual_effect']}"})
    if badges:
        item["badges"] = badges
    return item


def parse_spell_descriptions(
    asset: Dict[str, Any]
) -> Tuple[List[str], Dict[str, bool]]:
    lines: List[str] = []
    flags = {slug: False for slug in SPELL_FLAG_SLUGS.values()}
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
        if item.get("quality") not in ("Unique", "Normal", "Unusual"):
            parts.append(item["quality"])
    else:
        if item.get("quality") not in ("Unique", "Normal"):
            parts.append(item["quality"])
    base = item.get("base_name", "")
    if item.get("custom_name"):
        base = f"{item['custom_name']} | {base}"
    parts.append(base)
    if item.get("sheen"):
        parts.append(f"({item['sheen']})")
    return " ".join(p for p in parts if p)


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
    cleaned_map = items_game_cache.ITEM_BY_DEFINDEX or ld.ITEMS_GAME_CLEANED

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
                name = EFFECTS.get(int(effect_id))
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

        quality_id = asset.get("quality", 0)
        q_map = QUALITY_MAP.get(quality_id, {"name": "Unknown", "hex": "#B2B2B2"})
        q_name = schema_fetcher.QUALITIES.get(str(quality_id), q_map["name"])
        q_col = q_map["hex"]

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

        items.append(item)

    return items


def process_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Public wrapper that sorts items by name."""

    items = enrich_inventory(data)
    return sorted(items, key=lambda i: i["name"])
