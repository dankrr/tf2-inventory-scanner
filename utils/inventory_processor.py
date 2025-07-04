from typing import Any, Dict, List, Tuple, Iterable
import logging
import re
from html import unescape

import json
from pathlib import Path
import struct

from . import steam_api_client, local_data
from .constants import (
    KILLSTREAK_TIERS,
    SHEEN_NAMES,
    ORIGIN_MAP,
    PAINT_COLORS,
    KILLSTREAK_EFFECTS,
    KILLSTREAK_BADGE_ICONS,
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
    15: ("Decorated Weapon", "#FAFAFA"),
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


def _extract_killstreak(asset: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """Return killstreak tier and sheen names if present."""

    tier = None
    sheen = None
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        val = int(attr.get("float_value", 0))
        if idx == 2025:
            tier = local_data.KILLSTREAK_NAMES.get(str(val)) or KILLSTREAK_TIERS.get(
                val
            )
            if tier is None:
                logger.warning("Unknown killstreak tier id: %s", val)
        elif idx == 2014:
            sheen = SHEEN_NAMES.get(val)
            if sheen is None:
                logger.warning("Unknown sheen id: %s", val)
    return tier, sheen


def _extract_paint(asset: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """Return paint name and hex color if present."""

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx in (142, 261):
            val = int(attr.get("float_value", 0))
            name = local_data.PAINT_NAMES.get(str(val))
            hex_color = PAINT_COLORS.get(val, (None, None))[1]
            if not name:
                name = PAINT_COLORS.get(val, (None, None))[0]
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


def _decode_seed_info(attrs: Iterable[dict]) -> tuple[float | None, int | None]:
    """Return ``(wear_float, pattern_seed)`` from custom paintkit seed attrs."""

    lo = hi = None
    for attr in attrs:
        idx = attr.get("defindex")
        if idx == 866:
            lo = int(attr.get("value") or 0)
        elif idx == 867:
            hi = int(attr.get("value") or 0)
    if lo is None or hi is None:
        return None, None

    wear = struct.unpack("<f", struct.pack("<I", hi))[0]
    seed = lo
    if not (0 <= wear <= 1):
        wear = struct.unpack("<f", struct.pack("<I", lo))[0]
        seed = hi
    if not (0 <= wear <= 1):
        wear = None
    return wear, seed


def _extract_pattern_seed(asset: Dict[str, Any]) -> int | None:
    """Return pattern seed if present."""

    _, seed = _decode_seed_info(asset.get("attributes", []))
    return seed


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
                logger.warning("Invalid wear value: %r", raw)
                continue
            if not 0 <= val <= 1:
                logger.warning("Wear value out of range: %s", val)
            name = local_data.WEAR_NAMES.get(str(int(val)))
            return name or _wear_tier(val)

    wear_float, _ = _decode_seed_info(asset.get("attributes", []))
    if wear_float is not None:
        name = local_data.WEAR_NAMES.get(str(int(wear_float)))
        return name or _wear_tier(wear_float)

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
        if idx == 2013:
            val = int(attr.get("float_value", 0))
            name = local_data.KILLSTREAK_EFFECT_NAMES.get(
                str(val)
            ) or KILLSTREAK_EFFECTS.get(val)
            if name:
                return name
            logger.warning("Unknown killstreak effect id: %s", val)
    for desc in asset.get("descriptions", []):
        if not isinstance(desc, dict):
            continue
        text = unescape(desc.get("value", ""))
        text = re.sub(r"<[^>]+>", "", text)
        m = re.search(r"Killstreaker:?\s*(.+)", text, re.I)
        if m:
            return m.group(1).strip()
    return None


def _spell_icon(name: str) -> str:
    """Return an emoji icon for the given spell name."""

    lname = name.lower()
    if "foot" in lname:
        return "👣"
    if any(
        word in lname
        for word in (
            "paint",
            "pigment",
            "spectrum",
            "staining",
            "corruption",
            "chromatic",
            "die job",
            "color",
            "dye",
        )
    ):
        return "🖌"
    if any(
        word in lname
        for word in (
            "croon",
            "bark",
            "snarl",
            "growl",
            "moan",
            "bellow",
            "drawl",
            "bass",
        )
    ):
        return "🎤"
    if "pumpkin" in lname or "gourd" in lname or "squash" in lname:
        return "🎃"
    if "exorcism" in lname or "ghost" in lname:
        return "👻"
    if "fire" in lname:
        return "🔥"
    return "✨"


def _extract_spells(asset: Dict[str, Any]) -> tuple[list[dict], list[str]]:
    """Return badge dictionaries and spell names extracted from attributes."""

    badges: list[dict] = []
    names: list[str] = []

    attr_map = local_data.SCHEMA_ATTRIBUTES or {}

    for attr in asset.get("attributes", []):
        idx_raw = attr.get("defindex")
        try:
            idx = int(idx_raw)
        except (TypeError, ValueError):
            logger.warning("Invalid spell defindex: %r", idx_raw)
            continue

        info = attr_map.get(idx)
        if not isinstance(info, dict):
            continue

        name = info.get("description_string") or info.get("name")
        if not name:
            continue

        icon = _spell_icon(name)
        badges.append({"icon": icon, "title": name, "color": "#A156D6"})
        names.append(name)

    return badges, names


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
            name = local_data.STRANGE_PART_NAMES.get(defindex)
        if not name:
            continue
        lname = name.lower()
        if "strange part" in lname:
            part = name.split(":", 1)[-1].strip()
            if part and part not in parts:
                parts.append(part)
    return parts


def _extract_kill_eater_info(
    asset: Dict[str, Any],
) -> Tuple[Dict[int, int], Dict[int, int]]:
    """Return maps of kill-eater counts and score types keyed by index."""

    counts: Dict[int, int] = {}
    types: Dict[int, int] = {}

    for attr in asset.get("attributes", []):
        idx_raw = attr.get("defindex")
        try:
            idx = int(idx_raw)
        except (TypeError, ValueError):
            logger.warning("Invalid kill-eater defindex: %r", idx_raw)
            continue

        val_raw = (
            attr.get("float_value") if "float_value" in attr else attr.get("value")
        )
        try:
            val = int(float(val_raw))
        except (TypeError, ValueError):
            logger.warning("Invalid kill-eater value for %s: %r", idx, val_raw)
            continue

        if idx == 214:
            counts[1] = val
            continue
        if idx == 292:
            types[1] = val
            continue

        if idx >= 379:
            if idx % 2:  # odd -> kill_eater_X
                counts[(idx - 379) // 2 + 2] = val
            else:  # even -> score_type_X
                types[(idx - 380) // 2 + 2] = val
        elif idx in (214, 292):
            pass
        else:
            logger.warning("Unknown kill-eater index: %s", idx)

    return counts, types


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


def _is_placeholder_name(name: str) -> bool:
    """Return True if ``name`` looks like an internal placeholder."""

    lname = name.lower()
    if "tf_" in lname or "tf-" in lname or "weapon" in lname and " " not in name:
        return True
    if "_" in name:
        return True
    if lname in {"rifle", "smg", "pistol", "shotgun", "decoder ring"}:
        return True
    if name.isupper():
        return True
    return False


def _preferred_base_name(defindex: str, schema_entry: Dict[str, Any]) -> str:
    """Return human readable base item name."""

    if defindex in WARPAINT_MAP:
        return WARPAINT_MAP[defindex]

    name = schema_entry.get("item_name") or schema_entry.get("name")
    if name and not _is_placeholder_name(name):
        return name

    return name or f"Item #{defindex}"


def _process_item(asset: Dict[str, Any]) -> Dict[str, Any] | None:
    """Return an enriched item dictionary for a single asset."""

    defindex_raw = asset.get("defindex", 0)
    try:
        defindex_int = int(defindex_raw)
    except (TypeError, ValueError):
        logger.warning("Invalid defindex on asset: %r", defindex_raw)
        return None

    schema_entry = local_data.ITEMS_BY_DEFINDEX.get(defindex_int)
    if not schema_entry:
        logger.warning("Missing schema entry for defindex %s", defindex_int)
        return None

    defindex = str(defindex_int)
    image_url = schema_entry.get("image_url", "")

    paintkit_name = _extract_paintkit(asset)

    base_name = _preferred_base_name(defindex, schema_entry)
    if paintkit_name:
        base_name = f"{base_name} ({paintkit_name})"

    quality_id = asset.get("quality", 0)
    q_name, q_col = QUALITY_MAP.get(quality_id, ("Unknown", "#B2B2B2"))
    display_name = _build_item_name(base_name, q_name, asset)

    ks_tier, sheen = _extract_killstreak(asset)
    ks_effect = _extract_killstreak_effect(asset)
    ks_tier_val = None
    for attr in asset.get("attributes", []):
        if attr.get("defindex") == 2025:
            ks_tier_val = attr.get("float_value") or attr.get("value")
            break
    paint_name, paint_hex = _extract_paint(asset)
    wear_name = _extract_wear(asset)
    pattern_seed = _extract_pattern_seed(asset)
    crate_series_name = _extract_crate_series(asset)
    spell_badges, spells = _extract_spells(asset)
    strange_parts = _extract_strange_parts(asset)
    kill_eater_counts, score_types = _extract_kill_eater_info(asset)

    badges: List[Dict[str, str]] = []
    effect = _extract_unusual_effect(asset)
    if effect and quality_id in (5, 11):
        badges.append({"icon": "★", "title": effect, "color": "#8650AC"})
    if ks_tier_val:
        tier_id = int(float(ks_tier_val))
        icon = KILLSTREAK_BADGE_ICONS.get(tier_id)
        if icon:
            title = KILLSTREAK_TIERS[tier_id]
            badges.append({"icon": icon, "title": title, "color": "#ff7e30"})
    badges.extend(spell_badges)

    if paint_name:
        badges.append({"icon": "\U0001f3a8", "title": f"Paint: {paint_name}"})
    if paintkit_name:
        badges.append({"icon": "\U0001f58c", "title": f"Warpaint: {paintkit_name}"})

    item = {
        "defindex": defindex,
        "name": display_name,
        "quality": q_name,
        "quality_color": q_col,
        "image_url": image_url,
        "item_type_name": schema_entry.get("item_type_name"),
        "item_name": schema_entry.get("name"),
        "craft_class": schema_entry.get("craft_class"),
        "craft_material_type": schema_entry.get("craft_material_type"),
        "item_set": schema_entry.get("item_set"),
        "capabilities": schema_entry.get("capabilities"),
        "tags": schema_entry.get("tags"),
        "equip_regions": schema_entry.get("equip_regions")
        or schema_entry.get("equip_region"),
        "item_class": schema_entry.get("item_class"),
        "slot_type": schema_entry.get("item_slot") or schema_entry.get("slot_type"),
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
        "pattern_seed": pattern_seed,
        "paintkit_name": paintkit_name,
        "crate_series_name": crate_series_name,
        "killstreak_effect": ks_effect,
        "spells": spells,
        "badges": badges,  # always present, may be empty
        "strange_parts": strange_parts,
        "strange_count": kill_eater_counts.get(1),
        "score_type": (
            local_data.STRANGE_PART_NAMES.get(str(score_types.get(1)))
            if score_types.get(1) is not None
            else None
        ),
    }
    return item


def enrich_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a list of inventory items enriched with schema info."""
    items_raw = data.get("items")
    if not isinstance(items_raw, list):
        return []

    items: List[Dict[str, Any]] = []

    for asset in items_raw:
        item = _process_item(asset)
        if not item:
            continue

        spells_raw = item.get("spells", [])
        if isinstance(spells_raw, dict):
            spells_list = spells_raw.get("list", [])
        elif isinstance(spells_raw, list):
            spells_list = spells_raw
        else:
            spells_list = []

        item["modal_spells"] = spells_list
        item["spells"] = spells_list  # backward compatibility for JS
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
