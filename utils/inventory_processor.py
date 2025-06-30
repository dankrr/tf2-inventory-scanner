from typing import Any, Dict, List, Tuple
import logging
import re
from html import unescape

import json
from pathlib import Path

from . import (
    steam_api_client,
    schema_fetcher,
    items_game_cache,
    local_data,
    schema_manager,
)

logger = logging.getLogger(__name__)


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

HYBRID_SCHEMA: Dict[str, Any] | None = None


def _to_int(value: Any, default: int = 0) -> int:
    """Return ``value`` coerced to ``int`` or ``default`` on failure."""

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


# Backwards compatibility until all uses are updated
_safe_int = _to_int


def _get_hybrid_schema() -> Dict[str, Any]:
    global HYBRID_SCHEMA
    if HYBRID_SCHEMA is None:
        try:
            HYBRID_SCHEMA = schema_manager.load_hybrid_schema()
        except Exception:
            HYBRID_SCHEMA = {}
    return HYBRID_SCHEMA


BADGE_EMOJIS = {
    "paint": "\U0001f3a8",
    "killstreak": "\u2694\ufe0f",
    "sheen": "\u2728",
    "killstreaker": "\U0001f480",
    "festivized": "\U0001f384",
    "strange": "\U0001f4ca",
    "spell": "\U0001f47b",
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
            val = str(_to_int(attr.get("float_value")))
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


_KILLSTREAK_TIER = {
    1: "Killstreak",
    2: "Specialized",
    3: "Professional",
}

_SHEEN_NAMES = {
    1: "Team Shine",
    2: "Deadly Daffodil",
    3: "Mandarin",
    4: "Mean Green",
    5: "Villainous Violet",
    6: "Hot Rod",
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

# Map of paint ID -> (name, hex color)
PAINT_MAP = {
    3100495: ("A Color Similar to Slate", "#2F4F4F"),
    8208497: ("A Deep Commitment to Purple", "#7D4071"),
    8208498: ("A Distinctive Lack of Hue", "#141414"),
    1315860: ("An Extraordinary Abundance of Tinge", "#CF7336"),
    2960676: ("Color No. 216-190-216", "#D8BED8"),
    8289918: ("Dark Salmon Injustice", "#8847FF"),
    15132390: ("Drably Olive", "#808000"),
    8421376: ("Indubitably Green", "#729E42"),
    13595446: ("Mann Co. Orange", "#CF7336"),
    12377523: ("Muskelmannbraun", "#A57545"),
    5322826: ("Noble Hatter's Violet", "#51384A"),
    15787660: ("Pink as Hell", "#FF69B4"),
    15185211: ("A Mann's Mint", "#BCDDB3"),
}


def _extract_killstreak(asset: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """Return killstreak tier and sheen names if present."""

    tier = None
    sheen = None
    hybrid = _get_hybrid_schema()
    sheen_map = hybrid.get("sheens") or _SHEEN_NAMES
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        raw_val = attr.get("value", attr.get("float_value", 0))
        val = _to_int(raw_val)
        if idx == 2014:
            tier = _KILLSTREAK_TIER.get(val)
        elif idx == 2012:
            sheen = sheen_map.get(str(val)) or _SHEEN_NAMES.get(val)
    return tier, sheen


def _extract_paint(asset: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """Return paint name and hex color if present."""

    hybrid = _get_hybrid_schema()
    paint_map = {
        int(k): (v.get("name"), v.get("color"))
        for k, v in hybrid.get("paint_kits", {}).items()
        if isinstance(v, dict)
    } or PAINT_MAP
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx == 142:
            val = _to_int(attr.get("float_value"))
            return paint_map.get(val, PAINT_MAP.get(val, (None, None)))
    return None, None


def _build_item_name(base: str, quality: str, asset: Dict[str, Any]) -> str:
    """Return the display name prefixed with quality/effect."""

    parts: List[str] = []
    ks_tier, sheen = _extract_killstreak(asset)
    effect = _extract_unusual_effect(asset)

    if ks_tier:
        parts.append(ks_tier)

    if effect:
        parts.append(effect)
        if quality not in ("Unique", "Normal", "Unusual"):
            parts.append(quality)
    else:
        if quality not in ("Unique", "Normal"):
            parts.append(quality)

    parts.append(base)

    if sheen:
        parts.append(f"({sheen})")

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
    hybrid = _get_hybrid_schema()
    schema_map = (
        hybrid.get("items") or local_data.TF2_SCHEMA or schema_fetcher.SCHEMA or {}
    )
    cleaned_map = local_data.ITEMS_GAME_CLEANED or items_game_cache.ITEM_BY_DEFINDEX

    for asset in items_raw:
        defindex = str(asset.get("defindex", "0"))
        schema_entry = schema_map.get(defindex)
        ig_item = cleaned_map.get(defindex) or {}
        if not (schema_entry or ig_item):
            continue

        image_url = schema_entry.get("image_url") if schema_entry else ""

        # Prefer name from cleaned items_game if available
        base_name = (
            WARPAINT_MAP.get(defindex)
            or ig_item.get("name")
            or (schema_entry.get("item_name") if schema_entry else None)
            or (schema_entry.get("name") if schema_entry else None)
            or f"Item #{defindex}"
        )

        quality_id = asset.get("quality", 0)
        q_name, q_col = QUALITY_MAP.get(quality_id, ("Unknown", "#B2B2B2"))
        display_name = _build_item_name(base_name, q_name, asset)
        if asset.get("custom_name"):
            display_name = asset["custom_name"]

        ks_tier, sheen = _extract_killstreak(asset)
        paint_name, paint_hex = _extract_paint(asset)

        killstreaker = None
        festivized = False
        strange_parts: List[str] = []
        spells: List[str] = []
        _ks_list = hybrid.get("killstreakers", [])
        _ks_map: Dict[str, str] = {
            str(entry["id"]): entry["name"]
            for entry in _ks_list
            if isinstance(entry, dict) and "id" in entry and "name" in entry
        }
        parts_map = hybrid.get("strange_parts", {})
        for attr in asset.get("attributes", []):
            idx = attr.get("defindex")
            raw_val = attr.get("value", attr.get("float_value", 0))
            val = _to_int(raw_val)
            if idx == 2013:
                killstreaker = _ks_map.get(str(val))
            elif idx == 2053:
                festivized = bool(val)
            elif idx >= 382 and str(val) in parts_map:
                strange_parts.append(parts_map[str(val)])
            elif 1004 <= idx <= 1009:
                spells.append(str(idx))

        badges: List[Dict[str, str] | str] = []
        if paint_name:
            badges.append(BADGE_EMOJIS["paint"])
        if ks_tier:
            badges.append(BADGE_EMOJIS["killstreak"])
        if sheen:
            badges.append(BADGE_EMOJIS["sheen"])
        if killstreaker:
            badges.append(
                {"icon": "\U0001f480", "title": f"Killstreaker: {killstreaker}"}
            )
        if festivized:
            badges.append(BADGE_EMOJIS["festivized"])
        if q_name == "Strange" or strange_parts:
            badges.append(BADGE_EMOJIS["strange"])
        if spells:
            badges.append(BADGE_EMOJIS["spell"])

        item = {
            "defindex": defindex,
            "name": display_name,
            "base_name": base_name,
            "quality": q_name,
            "quality_color": q_col,
            "image_url": image_url,
            "item_type_name": (
                schema_entry.get("item_type_name")
                if schema_entry
                else ig_item.get("item_type_name")
            ),
            "item_name": (
                schema_entry.get("name") if schema_entry else ig_item.get("name")
            ),
            "craft_class": (
                schema_entry.get("craft_class")
                if schema_entry
                else ig_item.get("craft_class")
            ),
            "craft_material_type": (
                schema_entry.get("craft_material_type")
                if schema_entry
                else ig_item.get("craft_material_type")
            ),
            "item_set": schema_entry.get("item_set"),
            "capabilities": schema_entry.get("capabilities"),
            "tags": schema_entry.get("tags"),
            "equip_regions": ig_item.get("equip_regions")
            or ig_item.get("equip_region"),
            "item_class": ig_item.get("item_class"),
            "slot_type": ig_item.get("item_slot") or ig_item.get("slot_type"),
            "level": asset.get("level"),
            "origin": ORIGIN_MAP.get(asset.get("origin")),
            "killstreak_tier": ks_tier,
            "sheen": sheen,
            "paint_name": paint_name,
            "paint_hex": paint_hex,
            "killstreaker": killstreaker,
            "is_festivized": festivized,
            "strange_parts": strange_parts,
            "spells": spells,
            "badges": badges,
        }
        items.append(item)

        if len(items) <= 3:
            effect_id = asset.get("effect")
            ks = None
            sheen = None
            for attr in asset.get("attributes", []):
                idx = attr.get("defindex")
                val = _to_int(attr.get("float_value"))
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
