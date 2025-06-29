from typing import Any, Dict, List, Tuple
import logging
import re
from html import unescape

import json
from pathlib import Path

from . import steam_api_client, schema_fetcher, items_game_cache, local_data

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


_KILLSTREAK_TIER = {
    1: "Killstreak",
    2: "Specialized Killstreak",
    3: "Professional Killstreak",
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

# Map of attribute ID to Strange Part name (not exhaustive)
STRANGE_PART_MAP = {
    380: "Heavies Killed",
    381: "Buildings Destroyed",
    382: "Domination Kills",
    383: "Kills While Ubercharged",
    384: "Kills While Explosive Jumping",
}


def _extract_killstreak(asset: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """Return killstreak tier and sheen names if present."""

    tier = None
    sheen = None
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        val = int(attr.get("float_value", 0))
        if idx == 2025:
            tier = _KILLSTREAK_TIER.get(val)
        elif idx == 2014:
            sheen = _SHEEN_NAMES.get(val)
    return tier, sheen


def _extract_paint(asset: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """Return paint name and hex color if present."""

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx == 142:
            val = int(attr.get("float_value", 0))
            return PAINT_MAP.get(val, (None, None))
    return None, None


def _extract_killstreak_effect(asset: Dict[str, Any]) -> str | None:
    """Return killstreak effect string if present."""

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx in (2071, 2013):
            val = str(int(attr.get("float_value", 0)))
            name = local_data.EFFECT_NAMES.get(val)
            if name:
                return name

    for desc in asset.get("descriptions", []):
        if not isinstance(desc, dict):
            continue
        text = unescape(desc.get("value", ""))
        text = re.sub(r"<[^>]+>", "", text)
        m = re.search(r"Killstreaker:?\s*(.+)", text, re.I)
        if m:
            return m.group(1).strip()
    return None


def _extract_spells(asset: Dict[str, Any]) -> Tuple[List[str], Dict[str, bool]]:
    """Return spell lines and boolean flags for badge mapping."""

    lines: List[str] = []
    flags = {
        "has_exorcism": False,
        "has_paint_spell": False,
        "has_footprints": False,
        "has_pumpkin_bombs": False,
        "has_voice_lines": False,
    }
    SPELL_BITS = {
        1: ("Exorcism", "has_exorcism"),
        2: ("Paint Spell", "has_paint_spell"),
        4: ("Footprints", "has_footprints"),
        8: ("Pumpkin Bombs", "has_pumpkin_bombs"),
        16: ("Voices From Below", "has_voice_lines"),
    }

    for desc in asset.get("descriptions", []):
        if not isinstance(desc, dict):
            continue
        text = unescape(desc.get("value", ""))
        text = re.sub(r"<[^>]+>", "", text).strip()
        ltext = text.lower()
        if "halloween" in ltext or "spell" in ltext:
            lines.append(text)
        if "exorcism" in ltext:
            flags["has_exorcism"] = True
        if "paint" in ltext and "spell" in ltext:
            flags["has_paint_spell"] = True
        if "footprints" in ltext:
            flags["has_footprints"] = True
        if "pumpkin" in ltext:
            flags["has_pumpkin_bombs"] = True
        if "voices" in ltext or "rare spell" in ltext:
            flags["has_voice_lines"] = True

    for attr in asset.get("attributes", []):
        if attr.get("defindex") == 730:
            bitmask = int(attr.get("float_value", 0))
            for bit, (name, flag) in SPELL_BITS.items():
                if bitmask & bit:
                    if name not in lines:
                        lines.append(name)
                    flags[flag] = True
            break
    return lines, flags


def _extract_strange_parts(asset: Dict[str, Any]) -> List[str]:
    """Return a list of Strange Part names from attributes."""

    parts: List[str] = []
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        name = STRANGE_PART_MAP.get(idx)
        if name:
            parts.append(name)
    return parts


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


def generate_badges(
    item: Dict[str, Any], spell_flags: Dict[str, bool]
) -> List[Dict[str, str]]:
    """Return a list of badges for the given item."""

    badges: List[Dict[str, str]] = []
    if item.get("paint_name"):
        badges.append({"icon": "\U0001f3a8", "title": f"Painted: {item['paint_name']}"})
    if item.get("killstreak_tier"):
        badges.append({"icon": "\u2694\ufe0f", "title": item["killstreak_tier"]})
    if item.get("killstreak_effect"):
        badges.append(
            {
                "icon": "\U0001f480",
                "title": f"Killstreaker Effect: {item['killstreak_effect']}",
            }
        )
    if item.get("strange_parts"):
        badges.append({"icon": "\U0001f4ca", "title": "Strange Parts"})
    if item.get("unusual_effect"):
        badges.append(
            {"icon": "\U0001f30c", "title": f"Unusual: {item['unusual_effect']}"}
        )

    mapping = {
        "has_exorcism": ("\U0001f47b", "Exorcism"),
        "has_paint_spell": ("\U0001f3a8", "Paint spell"),
        "has_footprints": ("\U0001f463", "Footprints spell"),
        "has_pumpkin_bombs": ("\U0001f383", "Pumpkin Bombs"),
        "has_voice_lines": ("\u2728", "Rare spell"),
    }
    for key, (icon, title) in mapping.items():
        if spell_flags.get(key):
            badges.append({"icon": icon, "title": title})

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

        ks_tier, sheen = _extract_killstreak(asset)
        ks_effect = _extract_killstreak_effect(asset)
        paint_name, paint_hex = _extract_paint(asset)
        spell_lines, spell_flags = _extract_spells(asset)
        strange_parts = _extract_strange_parts(asset)
        unusual_effect = _extract_unusual_effect(asset)

        item = {
            "defindex": defindex,
            "name": display_name,
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
            "killstreak_effect": ks_effect,
            "spells": spell_lines,
            "strange_parts": strange_parts,
            "unusual_effect": unusual_effect,
        }
        badges = generate_badges(item, spell_flags)
        if badges:
            item["badges"] = badges
        items.append(item)

    return items


def process_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Public wrapper that sorts items by name."""
    items = enrich_inventory(data)
    return sorted(items, key=lambda i: i["name"])
