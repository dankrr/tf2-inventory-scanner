from typing import Any, Dict, List, Tuple
import logging
import re
from html import unescape

import json
from pathlib import Path

from . import steam_api_client, schema_fetcher, items_game_cache, local_data

items_game_cache.load_items_game_cleaned()

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
    15185211: ("A Mann's Mint", "#BCDDB3"),
    12955537: ("After Eight", "#2D2D24"),
    8289918: ("Dark Salmon Injustice", "#E9967A"),
    8421376: ("Indubitably Green", "#729E42"),
    13595446: ("Mann Co. Orange", "#CF7336"),
    12377523: ("Muskelmannbraun", "#A57545"),
    5322826: ("Noble Hatter's Violet", "#51384A"),
    15787660: ("Pink as Hell", "#FF69B4"),
    8154199: ("Peculiarly Drab Tincture", "#C5AF91"),
    4345659: ("Radigan Conagher Brown", "#694D3A"),
    2960676: ("Color No. 216-190-216", "#D8BED8"),
    7511618: ("The Bitter Taste of Defeat and Lime", "#32CD32"),
    15132390: ("Drably Olive", "#808000"),
    8422108: ("The Color of a Gentlemann's Business Pants", "#FBE85C"),
    12807213: ("Ye Olde Rustic Colour", "#7C6C57"),
    1315860: ("An Extraordinary Abundance of Tinge", "#E6E6E6"),
    12073019: ("Team Spirit", "#B8383B"),
    15787618: ("An Air of Debonair", "#654740"),
    8208496: ("Balaclavas Are Forever", "#3B1F23"),
    8208499: ("Cream Spirit", "#C36C2D"),
    1757009: ("Operator's Overalls", "#483838"),
    6901050: ("Waterlogged Lab Coat", "#A9B4C2"),
    2158218: ("Zepheniah's Greed", "#424F3B"),
    3874595: ("The Value of Teamwork", "#FFD700"),
    16341610: ("A Color Most Splendid", "#FFB000"),
    15158332: ("Australium Gold", "#E7B53B"),
    13164768: ("Aged Moustache Grey", "#7E7E7E"),
}


def _extract_killstreak(asset: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """Return killstreak tier and sheen names if present."""

    tier = None
    sheen = None
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        val = int(attr.get("float_value", 0))
        if idx in (2025, 2013):
            tier = local_data.KILLSTREAK_NAMES.get(str(val)) or _KILLSTREAK_TIER.get(
                val
            )
        elif idx == 2014:
            sheen = _SHEEN_NAMES.get(val)
    return tier, sheen


def _extract_paint(asset: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """Return paint name and hex color if present."""

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx in (142, 261):
            val = int(attr.get("float_value", 0))
            name = local_data.PAINT_NAMES.get(str(val))
            hex_color = PAINT_MAP.get(val, (None, None))[1]
            if not name:
                name = PAINT_MAP.get(val, (None, None))[0]
            if hex_color and not re.match(r"^#[0-9A-Fa-f]{6}$", hex_color):
                hex_color = None
            return name, hex_color
    return None, None


def _wear_tier(value: float) -> str:
    """Return a wear tier name for ``value`` between 0 and 1."""

    if value < 0.07:
        return "Factory New"
    if value < 0.15:
        return "Minimal Wear"
    if value < 0.38:
        return "Field-Tested"
    if value < 0.45:
        return "Well-Worn"
    return "Battle Scarred"


def _extract_wear(asset: Dict[str, Any]) -> str | None:
    """Return wear tier name if present."""

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx == 725:
            raw = attr.get("float_value")
            if raw is None:
                raw = attr.get("value")
            try:
                val = float(raw)
            except (TypeError, ValueError):
                continue
            name = local_data.WEAR_NAMES.get(str(int(val)))
            return name or _wear_tier(val)
    return None


def _extract_paintkit(asset: Dict[str, Any]) -> str | None:
    """Return paintkit name if present."""

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx == 834:
            val = int(attr.get("float_value", 0))
            return local_data.PAINTKIT_NAMES.get(str(val))
    return None


def _extract_crate_series(asset: Dict[str, Any]) -> str | None:
    """Return crate series name if present."""

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx == 187:
            val = int(attr.get("float_value", 0))
            return local_data.CRATE_SERIES_NAMES.get(str(val))
    return None


def _extract_killstreak_effect(asset: Dict[str, Any]) -> str | None:
    """Return killstreak effect string if present."""

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx in (2013, 2015):
            name = attr.get("account_info", {}).get("name")
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


def _extract_spells(
    asset: Dict[str, Any]
) -> Tuple[List[Dict[str, str]], Dict[str, bool]]:
    """Return spell details and boolean flags for badge mapping."""

    spells: List[Dict[str, str]] = []
    flags = {
        "has_exorcism": False,
        "has_paint_spell": False,
        "has_footprints": False,
        "has_pumpkin_bombs": False,
        "has_voice_lines": False,
    }

    for desc in asset.get("descriptions", []):
        if not isinstance(desc, dict):
            continue
        text = unescape(desc.get("value", ""))
        text = re.sub(r"<[^>]+>", "", text).strip()
        if not text:
            continue

        ltext = text.lower()
        if "halloween" in ltext or "spell" in ltext:
            name = text.split(":", 1)[-1].strip()
            category: str | None = None
            if "exorcism" in ltext or "pumpkin" in ltext:
                category = "weapon"
            elif "paint" in ltext and "spell" in ltext:
                category = "paint"
            elif "footprints" in ltext:
                category = "footprint"
            elif "voices" in ltext or "rare spell" in ltext:
                category = "vocal"
            if category:
                spells.append({"category": category, "name": name})
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

    return spells, flags


def _extract_strange_parts(asset: Dict[str, Any]) -> List[str]:
    """Return list of Strange Part names from attributes if present."""

    parts: List[str] = []
    for attr in asset.get("attributes", []):
        info = attr.get("account_info")
        name = None
        if isinstance(info, dict):
            name = info.get("name")
        if not name:
            defindex = str(attr.get("defindex"))
            entry = items_game_cache.ITEM_BY_DEFINDEX.get(defindex)
            if isinstance(entry, dict):
                name = entry.get("name")
            if not name:
                name = local_data.STRANGE_PART_NAMES.get(defindex)
        if not name:
            continue
        lname = name.lower()
        if "strange part" in lname:
            part = name.split(":", 1)[-1].strip()
            if part and part not in parts:
                parts.append(part)
    return parts


def _build_item_name(base: str, quality: str, asset: Dict[str, Any]) -> str:
    """Return the display name prefixed with quality and killstreak info."""

    parts: List[str] = []
    ks_tier, sheen = _extract_killstreak(asset)

    if ks_tier:
        parts.append(ks_tier)

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


def _process_item(
    asset: Dict[str, Any], schema_map: Dict[str, Any], cleaned_map: Dict[str, Any]
) -> Dict[str, Any] | None:
    """Return an enriched item dictionary for a single asset."""

    defindex = str(asset.get("defindex", "0"))
    schema_entry = schema_map.get(defindex)
    ig_item = cleaned_map.get(defindex) or {}
    if not (schema_entry or ig_item):
        return None

    image_url = schema_entry.get("image_url") if schema_entry else ""

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
    wear_name = _extract_wear(asset)
    paintkit_name = _extract_paintkit(asset)
    crate_series_name = _extract_crate_series(asset)
    spells, spell_flags = _extract_spells(asset)
    strange_parts = _extract_strange_parts(asset)

    badges: List[Dict[str, str]] = []
    effect = _extract_unusual_effect(asset)
    if effect and quality_id in (5, 11):
        badges.append({"icon": "★", "title": effect, "color": "#8650AC"})
    if ks_effect:
        badges.append({"icon": "⚔", "title": f"Killstreaker: {ks_effect}"})
    category_flags = {
        "weapon": spell_flags.get("has_exorcism")
        or spell_flags.get("has_pumpkin_bombs"),
        "paint": spell_flags.get("has_paint_spell"),
        "footprint": spell_flags.get("has_footprints"),
        "vocal": spell_flags.get("has_voice_lines"),
    }
    for cat, present in category_flags.items():
        if not present:
            continue
        icon_map = {
            "weapon": "\U0001f47b",
            "vocal": "\U0001f5e3\ufe0f",
            "paint": "\U0001fa9f",
            "footprint": "\U0001f463",
        }
        title_map = {
            "weapon": "Weapon spell",
            "vocal": "Vocal spell",
            "paint": "Paint spell",
            "footprint": "Footprints spell",
        }
        badges.append({"icon": icon_map[cat], "title": title_map[cat]})

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
        "item_name": schema_entry.get("name") if schema_entry else ig_item.get("name"),
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
        "equip_regions": ig_item.get("equip_regions") or ig_item.get("equip_region"),
        "item_class": ig_item.get("item_class"),
        "slot_type": ig_item.get("item_slot") or ig_item.get("slot_type"),
        "level": asset.get("level"),
        "origin": ORIGIN_MAP.get(asset.get("origin")),
        "custom_name": asset.get("custom_name"),
        "custom_description": asset.get("custom_desc"),
        "unusual_effect": effect if quality_id in (5, 11) else None,
        "killstreak_tier": ks_tier,
        "sheen": sheen,
        "paint_name": paint_name,
        "paint_hex": paint_hex,
        "wear_name": wear_name,
        "paintkit_name": paintkit_name,
        "crate_series_name": crate_series_name,
        "killstreak_effect": ks_effect,
        "spells": spells,
        "badges": badges,  # always present, may be empty
        "strange_parts": strange_parts,
    }
    return item


def enrich_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a list of inventory items enriched with schema info."""
    items_raw = data.get("items")
    if not isinstance(items_raw, list):
        return []

    items: List[Dict[str, Any]] = []
    schema_map = local_data.TF2_SCHEMA or schema_fetcher.SCHEMA or {}
    cleaned_map = local_data.ITEMS_GAME_CLEANED or items_game_cache.ITEM_BY_DEFINDEX

    icon_map = {
        "weapon": "\U0001f47b",
        "vocal": "\U0001f5e3\ufe0f",
        "paint": "\U0001fa9f",
        "footprint": "\U0001f463",
    }

    for asset in items_raw:
        item = _process_item(asset, schema_map, cleaned_map)
        if item:
            modal_spells = [
                f"{icon_map.get(spell.get('category'), '')} {spell.get('name')}"
                for spell in item.get("spells", [])
            ]
            item["modal_spells"] = modal_spells
            item["spells"] = modal_spells  # backward compatibility for JS
            items.append(item)

    return items


def process_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Public wrapper that sorts items by name."""
    items = enrich_inventory(data)
    return sorted(items, key=lambda i: i["name"])


def run_enrichment_test(path: str | None = None) -> None:
    """Load a local inventory JSON file, enrich it, and print the result.

    This helper is intended for manual debugging of the enrichment logic. It
    loads ``converted.json`` next to this module (or the file provided via
    ``path``), processes the inventory with :func:`process_inventory`, and
    prints the enriched items as pretty JSON.
    """

    if path is None:
        file_path = Path(__file__).with_name("converted.json")
    else:
        file_path = Path(path)

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    local_data.load_files()
    with file_path.open() as f:
        raw = json.load(f)

    items = process_inventory(raw)
    print(json.dumps(items, indent=2))


if __name__ == "__main__":  # pragma: no cover - manual debug helper
    run_enrichment_test()
