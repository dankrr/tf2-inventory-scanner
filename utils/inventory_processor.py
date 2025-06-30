from typing import Any, Dict, List, Tuple
import logging
import re
from html import unescape

import json
from pathlib import Path

from . import steam_api_client, schema_fetcher, items_game_cache
import utils.local_data as ld

logger = logging.getLogger(__name__)


# Mapping of defindex -> human readable name for warpaints
MAPPING_FILE = Path(__file__).with_name("warpaint_mapping.json")
WARPAINT_MAP: Dict[str, str] = {}
if MAPPING_FILE.exists():
    with MAPPING_FILE.open() as f:
        WARPAINT_MAP = json.load(f)

# Fallback lookup tables used when local_data is empty
DEFAULT_QUALITY_COLORS = {11: "#CF6A32"}
DEFAULT_SPELL_FLAGS = {1: "Exorcism", 4: "Footprints"}

# Attribute handlers populated below
ATTRIBUTE_HANDLERS: Dict[int, callable] = {}


def _extract_unusual_effect(asset: Dict[str, Any]) -> str | None:
    """Return the unusual effect name from attributes or descriptions."""

    if "effect" in asset:
        name = ld.EFFECTS.get(int(asset["effect"]))
        if name:
            return name

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx == 134:
            val = str(int(attr.get("float_value", 0)))
            name = ld.EFFECTS.get(int(val))
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


_KILLSTREAK_TIER = {1: "Killstreak", 2: "Specialized", 3: "Professional"}


# Map of item origin ID -> human readable string


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
            sheen = ld.SHEENS.get(val)
    return tier, sheen


def _extract_paint(asset: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """Return paint name and hex color if present."""

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx == 142:
            val = int(attr.get("float_value", 0))
            paint = ld.PAINTS.get(val)
            if paint:
                return paint.get("name"), paint.get("hex")
    return None, None


def _extract_killstreak_effect(asset: Dict[str, Any]) -> str | None:
    """Return killstreak effect string if present."""

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx in (2071, 2013):
            val = str(int(attr.get("float_value", 0)))
            name = ld.EFFECTS.get(int(val)) or ld.EFFECT_NAMES.get(str(int(val)))
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
    mapping = ld.SPELL_FLAGS or DEFAULT_SPELL_FLAGS
    SPELL_BITS = {
        bit: (name, name.lower().replace(" ", "_")) for bit, name in mapping.items()
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
        name = ld.STRANGE_PARTS.get(idx)
        if name:
            parts.append(name)
    return parts


def handle_custom_name(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    name = attr.get("value") or attr.get("string_value")
    if name:
        item["custom_name"] = str(name)


def handle_paint_color(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    val = int(attr.get("float_value", 0))
    paint = ld.PAINTS.get(val)
    if paint:
        item["paint_name"] = paint.get("name")
        item["paint_hex"] = paint.get("hex")


def handle_spell_bitmask(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    bitmask = int(attr.get("float_value", 0))
    for bit, name in ld.SPELL_FLAGS.items():
        if bitmask & bit:
            item.setdefault("spells", []).append(name)
            flag = name.lower().replace(" ", "_")
            item.setdefault("spell_flags", {})[flag] = True


def handle_killstreak_tier(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    tier = int(attr.get("float_value", 0))
    item["killstreak_tier"] = _KILLSTREAK_TIER.get(tier)


def handle_sheen(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    item["sheen"] = ld.SHEENS.get(int(attr.get("float_value", 0)))


def handle_killstreaker(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    item["killstreaker"] = ld.KILLSTREAKERS.get(int(attr.get("float_value", 0)))


def handle_strange_part(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    name = ld.STRANGE_PARTS.get(attr.get("defindex"))
    if name:
        item.setdefault("strange_parts", []).append(name)


def handle_festivized(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    item["is_festivized"] = bool(int(attr.get("float_value", 0)))


def handle_unusual_effect(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    item["unusual_effect"] = ld.EFFECTS.get(int(attr.get("float_value", 0)))


ATTRIBUTE_HANDLERS.update(
    {
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
        2041: handle_festivized,
        2042: handle_festivized,
        2043: handle_festivized,
        2044: handle_festivized,
        214: handle_unusual_effect,
    }
)


def _decode_attributes(asset: Dict[str, Any], item: Dict[str, Any]) -> None:
    for attr in asset.get("attributes", []):
        defindex = attr.get("defindex")
        handler = ATTRIBUTE_HANDLERS.get(defindex)
        if handler:
            handler(item, attr)
        else:
            item.setdefault("misc_attrs", []).append(attr)
    if not item.get("spells"):
        lines, flags = _extract_spells(asset)
        item["spells"] = lines
        item.setdefault("spell_flags", {}).update(flags)


def _build_display_name(quality: str, item: Dict[str, Any]) -> str:
    """Return the final item name based on stored base_name."""

    base = item.get("custom_name") or item.get("base_name", "")

    parts: List[str] = []
    if item.get("killstreak_tier"):
        parts.append(item["killstreak_tier"])

    if item.get("unusual_effect"):
        parts.append(item["unusual_effect"])
        if quality not in ("Unique", "Normal", "Unusual"):
            parts.append(quality)
    else:
        if quality not in ("Unique", "Normal"):
            parts.append(quality)

    parts.append(base)

    if item.get("sheen"):
        parts.append(f"({item['sheen']})")

    return " ".join(parts)


def generate_badges(item: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return a list of badge metadata."""

    flags = item.get("spell_flags", {})
    badges: List[Dict[str, str]] = []

    if item.get("paint_name"):
        badges.append({"icon": "🎨", "title": f"Painted: {item['paint_name']}"})
    if item.get("killstreak_tier"):
        badges.append({"icon": "⚔️", "title": item["killstreak_tier"]})
    if item.get("killstreaker"):
        badges.append({"icon": "💀", "title": item["killstreaker"]})
    if item.get("sheen"):
        badges.append({"icon": "✨", "title": f"Sheen: {item['sheen']}"})
    if flags.get("footprints"):
        badges.append({"icon": "👣", "title": "Footprints spell"})
    if flags.get("exorcism"):
        badges.append({"icon": "👻", "title": "Exorcism"})
    if flags.get("pumpkin_bombs"):
        badges.append({"icon": "🎃", "title": "Pumpkin Bombs"})
    if flags.get("voices_from_below"):
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
    schema_map = ld.TF2_SCHEMA or schema_fetcher.SCHEMA or {}
    cleaned_map = ld.ITEMS_GAME_CLEANED or items_game_cache.ITEM_BY_DEFINDEX

    for asset in items_raw:
        defindex = str(asset.get("defindex", "0"))
        schema_entry = schema_map.get(defindex)
        ig_item = cleaned_map.get(defindex) or {}
        if not (schema_entry or ig_item):
            continue

        image_url = schema_entry.get("image_url") if schema_entry else ""

        # Resolve base_name with fallbacks in priority order
        base_name = (
            WARPAINT_MAP.get(defindex)
            or ig_item.get("name")
            or (schema_entry.get("item_name") if schema_entry else None)
            or (schema_entry.get("name") if schema_entry else None)
        )
        if not base_name:
            base_name = f"Unknown Item ({defindex})"
            logger.warning("Unknown base name for defindex %s", defindex)

        quality_id = asset.get("quality", 0)
        q_name = schema_fetcher.QUALITIES.get(str(quality_id))
        if not q_name:
            if quality_id == 0:
                q_name = "Normal"
            else:
                q_name = ld.QUALITY_MAP.get(quality_id, ("Unknown",))[0]
        q_col = ld.QUALITY_MAP.get(quality_id, (None, None))[1]
        if not q_col:
            q_col = DEFAULT_QUALITY_COLORS.get(quality_id, "#B2B2B2")

        item: Dict[str, Any] = {
            "defindex": defindex,
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
            "origin": ld.ORIGIN_MAP.get(asset.get("origin")),
        }

        item["base_name"] = base_name

        _decode_attributes(asset, item)
        if "killstreak_effect" not in item:
            ks_effect = _extract_killstreak_effect(asset)
            if ks_effect:
                item["killstreak_effect"] = ks_effect
        if "unusual_effect" not in item:
            item["unusual_effect"] = _extract_unusual_effect(asset)

        item["name"] = _build_display_name(q_name, item)

        badges = generate_badges(item)
        if badges:
            item["badges"] = badges
        items.append(item)

    return items


def process_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Public wrapper that sorts items by name."""
    items = enrich_inventory(data)
    return sorted(items, key=lambda i: i["name"])
