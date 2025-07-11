from typing import Any, Dict, List, Tuple
import logging
import re
from html import unescape

import json
from pathlib import Path

from . import steam_api_client, local_data
from .helpers import best_match_from_keys
from .valuation_service import ValuationService, get_valuation_service
from .wear_helpers import _wear_tier, _decode_seed_info
from .constants import (
    KILLSTREAK_TIERS,
    KILLSTREAK_LABELS,
    SHEEN_NAMES,
    KILLSTREAK_SHEEN_COLORS,
    ORIGIN_MAP,
    PAINT_COLORS,
    KILLSTREAK_EFFECTS,
    KILLSTREAK_BADGE_ICONS,
    SPELL_MAP,
)


logger = logging.getLogger(__name__)


SCHEMA_DIR = Path("cache/schema")
try:  # graceful fallback if the optional file is missing
    with open(SCHEMA_DIR / "strange_parts.json") as fp:
        _PARTS_BY_ID = {int(v[2:]): k for k, v in json.load(fp).items()}
except FileNotFoundError:  # pragma: no cover - only used in dev/test
    _PARTS_BY_ID = {}


# ---------------------------------------------------------------------------
# attribute class helpers

# Sets derived from ``local_data.SCHEMA_ATTRIBUTES``. They may be empty if
# schema data has not been loaded yet.
UNUSUAL_CLASSES: set[str] = set()
KILLSTREAK_TIER_CLASSES: set[str] = set()
KILLSTREAK_SHEEN_CLASSES: set[str] = set()
KILLSTREAK_EFFECT_CLASSES: set[str] = set()
PAINT_CLASSES: set[str] = set()
WEAR_CLASSES: set[str] = set()
PATTERN_SEED_LO_CLASSES: set[str] = set()
PATTERN_SEED_HI_CLASSES: set[str] = set()
PAINTKIT_CLASSES: set[str] = set()
CRATE_SERIES_CLASSES: set[str] = set()

# Origins configuration loaded from ``static/exclusions.json`` via ``local_data``
_exclusions = local_data.load_exclusions()
CRAFT_WEAPON_ALLOWED_ORIGINS = set(_exclusions.get("craft_weapon_exclusions", []))

# Sets of attribute defindexes considered "special" for craft weapon detection
SPECIAL_SPELL_ATTRS: set[int] = set(SPELL_MAP.keys()) | set(range(8900, 8926))
SPECIAL_KILLSTREAK_ATTRS: set[int] = {2013, 2014, 2025}
SPECIAL_FESTIVIZER_ATTRS: set[int] = {2053}
SPECIAL_PAINTKIT_ATTRS: set[int] = {834, 866, 867, 725, 749}


def _refresh_attr_classes() -> None:
    """Populate attribute class sets from ``local_data.SCHEMA_ATTRIBUTES``."""

    mapping = local_data.SCHEMA_ATTRIBUTES or {}

    def cls(idx: int) -> str | None:
        info = mapping.get(idx)
        if isinstance(info, dict):
            return info.get("attribute_class")
        return None

    global UNUSUAL_CLASSES, KILLSTREAK_TIER_CLASSES, KILLSTREAK_SHEEN_CLASSES
    global KILLSTREAK_EFFECT_CLASSES, PAINT_CLASSES, WEAR_CLASSES
    global PATTERN_SEED_LO_CLASSES, PATTERN_SEED_HI_CLASSES
    global PAINTKIT_CLASSES, CRATE_SERIES_CLASSES

    UNUSUAL_CLASSES = {cls(134), cls(2041)} - {None}
    KILLSTREAK_TIER_CLASSES = {cls(2025)} - {None}
    KILLSTREAK_SHEEN_CLASSES = {cls(2014)} - {None}
    KILLSTREAK_EFFECT_CLASSES = {cls(2013)} - {None}
    PAINT_CLASSES = {cls(142), cls(261)} - {None}
    WEAR_CLASSES = {cls(725), cls(749)} - {None}
    PATTERN_SEED_LO_CLASSES = {cls(866)} - {None}
    PATTERN_SEED_HI_CLASSES = {cls(867)} - {None}
    PAINTKIT_CLASSES = {cls(834)} - {None}
    CRATE_SERIES_CLASSES = {cls(187)} - {None}


_refresh_attr_classes()


def _get_attr_class(idx: Any) -> str | None:
    """Return the attribute class string for ``idx`` using the cached schema."""

    try:
        idx_int = int(idx)
    except (TypeError, ValueError):
        return None
    info = local_data.SCHEMA_ATTRIBUTES.get(idx_int)
    if isinstance(info, dict):
        return info.get("attribute_class")
    return None


# Map of quality ID to (name, background color)
QUALITY_MAP = {
    0: ("Normal", "#7f7f7f"),
    1: ("Genuine", "#273429"),
    3: ("Vintage", "#28344a"),
    5: ("Unusual", "#4f3363"),
    6: ("Unique", "#957e04"),
    11: ("Strange", "#7a4121"),
    13: ("Haunted", "#0c8657"),
    14: ("Collector's", "#1c0101"),
    15: ("Decorated Weapon", "#949494"),
}

# effect_id -> name mapping loaded from ``local_data``
EFFECTS_MAP: Dict[int, str] = {
    int(k): v for k, v in getattr(local_data, "EFFECT_NAMES", {}).items()
}


def _extract_unusual_effect(asset: Dict[str, Any]) -> dict | None:
    """Return unusual effect mapping for Unusual items."""

    # Only Unusual quality (5) items can have a particle effect.
    if asset.get("quality") != 5:
        return None

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        try:
            idx_int = int(idx)
        except (TypeError, ValueError):
            continue

        if idx_int not in (134, 2041):
            continue

        raw = attr.get("float_value")
        effect_id = None
        if raw is not None:
            try:
                effect_id = int(float(raw))
            except (TypeError, ValueError):
                effect_id = None

        if not effect_id:
            raw = attr.get("value")
            try:
                effect_id = int(float(raw)) if raw is not None else None
            except (TypeError, ValueError):
                continue

        if not effect_id:
            continue

        effect_name = local_data.EFFECT_NAMES.get(str(effect_id)) or EFFECTS_MAP.get(
            effect_id
        )
        return {"id": effect_id, "name": effect_name}

    return None


def _extract_killstreak_tier(asset: Dict[str, Any]) -> int | None:
    """Return killstreak tier id if present."""

    _refresh_attr_classes()
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = _get_attr_class(idx)
        if attr_class in KILLSTREAK_TIER_CLASSES or idx == 2025:
            raw = (
                attr.get("float_value") if "float_value" in attr else attr.get("value")
            )
            try:
                val = int(float(raw)) if raw is not None else None
            except (TypeError, ValueError):
                logger.warning("Invalid killstreak tier value: %r", raw)
                continue
            if val is not None and val not in KILLSTREAK_TIERS:
                logger.warning("Unknown killstreak tier id: %s", val)
            return val

    for desc in asset.get("descriptions", []):
        if not isinstance(desc, dict):
            continue
        text = unescape(desc.get("value", ""))
        text = re.sub(r"<[^>]+>", "", text)
        if re.search(r"Professional Killstreak", text, re.I):
            return 3
        if re.search(r"Specialized Killstreak", text, re.I):
            return 2
        if re.search(r"Killstreaks? Active", text, re.I):
            return 1

    return None


def _extract_killstreak(
    asset: Dict[str, Any],
) -> Tuple[str | None, str | None, int | None]:
    """Return killstreak tier name, sheen name and sheen id if present."""

    _refresh_attr_classes()
    tier = None
    sheen = None
    sheen_id = None
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        val_raw = (
            attr.get("float_value") if "float_value" in attr else attr.get("value")
        )
        try:
            val = int(float(val_raw)) if val_raw is not None else None
        except (TypeError, ValueError):
            logger.debug("Invalid killstreak attribute value: %r", val_raw)
            continue
        attr_class = _get_attr_class(idx)
        if attr_class in KILLSTREAK_TIER_CLASSES:
            tier = local_data.KILLSTREAK_NAMES.get(str(val)) or KILLSTREAK_TIERS.get(
                val
            )
            if tier is None:
                logger.warning("Unknown killstreak tier id: %s", val)
        elif attr_class in KILLSTREAK_SHEEN_CLASSES:
            sheen_id = val
            sheen = SHEEN_NAMES.get(val)
            if sheen is None:
                logger.warning("Unknown sheen id: %s", val)
        elif idx in (2025, 2014):
            logger.warning("Using numeric fallback for killstreak index %s", idx)
            if idx == 2025:
                tier = local_data.KILLSTREAK_NAMES.get(
                    str(val)
                ) or KILLSTREAK_TIERS.get(val)
                if tier is None:
                    logger.warning("Unknown killstreak tier id: %s", val)
            else:
                sheen_id = val
                sheen = SHEEN_NAMES.get(val)
                if sheen is None:
                    logger.warning("Unknown sheen id: %s", val)
    return tier, sheen, sheen_id


def _extract_paint(asset: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """Return paint name and hex color if present."""

    _refresh_attr_classes()
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = _get_attr_class(idx)
        if attr_class in PAINT_CLASSES:
            val = int(attr.get("float_value", 0))
            name = local_data.PAINT_NAMES.get(str(val))
            hex_color = PAINT_COLORS.get(val, (None, None))[1]
            if not name:
                name = PAINT_COLORS.get(val, (None, None))[0]
            if hex_color and not re.match(r"^#[0-9A-Fa-f]{6}$", hex_color):
                hex_color = None
            return name, hex_color
        elif idx in (142, 261):
            logger.warning("Using numeric fallback for paint index %s", idx)
            val = int(attr.get("float_value", 0))
            name = local_data.PAINT_NAMES.get(str(val))
            hex_color = PAINT_COLORS.get(val, (None, None))[1]
            if not name:
                name = PAINT_COLORS.get(val, (None, None))[0]
            if hex_color and not re.match(r"^#[0-9A-Fa-f]{6}$", hex_color):
                hex_color = None
            return name, hex_color
    return None, None


def _extract_pattern_seed(asset: Dict[str, Any]) -> int | None:
    """Return pattern seed if present."""

    _, seed = _decode_seed_info(asset.get("attributes", []))
    return seed


def _extract_wear(asset: Dict[str, Any]) -> str | None:
    """Return wear tier name if present."""

    _refresh_attr_classes()
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = _get_attr_class(idx)
        if attr_class in WEAR_CLASSES:
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
        elif idx in (725, 749):
            logger.warning("Using numeric fallback for wear index %s", idx)
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


def _extract_wear_float(asset: Dict[str, Any]) -> float | None:
    """Return wear float value if present."""

    _refresh_attr_classes()
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = _get_attr_class(idx)
        if attr_class in WEAR_CLASSES or idx in (725, 749):
            raw = attr.get("float_value")
            if raw is None:
                raw = attr.get("value")
            try:
                val = float(raw)
            except (TypeError, ValueError):
                logger.warning("Invalid wear value: %r", raw)
                continue
            if 0 <= val <= 1:
                return val

    wear_float, _ = _decode_seed_info(asset.get("attributes", []))
    if wear_float is not None and 0 <= wear_float <= 1:
        return wear_float
    return None


def _slug_to_paintkit_name(slug: str) -> str:
    """Return a human readable paintkit name from schema slug."""

    if slug.endswith("_mk_ii"):
        base = slug[:-6]
        return base.replace("_", " ").title() + " Mk.II"
    return slug.replace("_", " ").title()


def _extract_paintkit(
    asset: Dict[str, Any], schema_entry: Dict[str, Any]
) -> tuple[int | None, str | None]:
    """Return ``(paintkit_id, name)`` or ``(None, None)`` if not present."""

    _refresh_attr_classes()
    paintkit_id = None
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = _get_attr_class(idx)
        if idx == 834 or attr_class in PAINTKIT_CLASSES:
            raw = attr.get("value")
            if raw is None:
                raw = attr.get("float_value")
            try:
                paintkit_id = int(float(raw)) if raw is not None else None
            except (TypeError, ValueError):
                logger.warning("Invalid paintkit id: %r", raw)
                paintkit_id = None
                continue
            if paintkit_id is not None:
                if idx == 834 and attr_class not in PAINTKIT_CLASSES:
                    logger.warning("Using numeric fallback for paintkit index %s", idx)
                name = local_data.PAINTKIT_NAMES_BY_ID.get(str(paintkit_id))
                return paintkit_id, (name or "Unknown")

    if paintkit_id is None:
        for attr in asset.get("attributes", []):
            idx = attr.get("defindex")
            if idx == 749:
                raw = attr.get("value")
                if raw is None:
                    raw = attr.get("float_value")
                try:
                    paintkit_id = int(float(raw)) if raw is not None else None
                except (TypeError, ValueError):
                    logger.warning("Invalid paintkit id: %r", raw)
                    continue
                if paintkit_id is not None:
                    logger.warning("Using numeric fallback for paintkit index %s", idx)
                    name = local_data.PAINTKIT_NAMES_BY_ID.get(str(paintkit_id))
                    return paintkit_id, (name or "Unknown")

    schema_name = schema_entry.get("name")
    if isinstance(schema_name, str):
        prefixes = (
            "warbird_",
            "concealedkiller_",
            "craftsmann_",
        )
        for prefix in prefixes:
            if schema_name.startswith(prefix):
                suffix = schema_name[len(prefix) :]
                parts = suffix.split("_", 1)
                if len(parts) == 2:
                    paint_slug = parts[1]
                else:
                    paint_slug = suffix
                warpaint_name = _slug_to_paintkit_name(paint_slug)
                warpaint_id = local_data.PAINTKIT_NAMES.get(warpaint_name)
                if warpaint_id is None:
                    match = best_match_from_keys(
                        warpaint_name, local_data.PAINTKIT_NAMES.keys()
                    )
                    if match:
                        warpaint_id = local_data.PAINTKIT_NAMES.get(match)
                        warpaint_name = match
                if warpaint_id is not None:
                    return warpaint_id, warpaint_name
                break

    return None, None


def _extract_crate_series(asset: Dict[str, Any]) -> str | None:
    """Return crate series name if present."""

    _refresh_attr_classes()
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = _get_attr_class(idx)
        if attr_class in CRATE_SERIES_CLASSES:
            val = int(attr.get("float_value", 0))
            return local_data.CRATE_SERIES_NAMES.get(str(val))
        elif idx == 187:
            logger.warning("Using numeric fallback for crate series index %s", idx)
            val = int(attr.get("float_value", 0))
            return local_data.CRATE_SERIES_NAMES.get(str(val))
    return None


def _extract_australium(asset: Dict[str, Any]) -> bool:
    """Return True if the asset has an Australium attribute."""

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        try:
            if int(idx) == 2027:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _extract_killstreak_effect(asset: Dict[str, Any]) -> str | None:
    """Return killstreak effect string if present."""

    _refresh_attr_classes()
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = _get_attr_class(idx)
        if attr_class in KILLSTREAK_EFFECT_CLASSES:
            val = int(attr.get("float_value", 0))
            name = local_data.KILLSTREAK_EFFECT_NAMES.get(
                str(val)
            ) or KILLSTREAK_EFFECTS.get(val)
            if name:
                return name
            logger.warning("Unknown killstreak effect id: %s", val)
        elif idx == 2013:
            logger.warning("Using numeric fallback for killstreak effect index %s", idx)
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

    for attr in asset.get("attributes", []):
        idx_raw = attr.get("defindex")
        try:
            idx = int(idx_raw)
        except (TypeError, ValueError):
            logger.warning("Invalid spell defindex: %r", idx_raw)
            continue

        mapping = SPELL_MAP.get(idx)
        if not mapping:
            continue

        raw = attr.get("float_value") if "float_value" in attr else attr.get("value")
        try:
            val = int(float(raw)) if raw is not None else None
        except (TypeError, ValueError):
            val = None
        if val is None or val not in mapping:
            continue

        name = mapping[val]
        icon = _spell_icon(name)
        badges.append(
            {
                "icon": icon,
                "title": name,
                "color": "#A156D6",
                "label": name,
                "type": "spell",
            }
        )
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
            # Ignore non-numeric defindex values
            continue

        val_raw = (
            attr.get("float_value") if "float_value" in attr else attr.get("value")
        )
        try:
            val = int(float(val_raw))
        except (TypeError, ValueError):
            # Ignore non-numeric values
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

    return counts, types


def _build_item_name(base: str, quality: str, asset: Dict[str, Any]) -> str:
    """Return the display name prefixed with quality and killstreak info."""

    parts: List[str] = []
    ks_tier, sheen, _ = _extract_killstreak(asset)

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

    name = schema_entry.get("item_name") or schema_entry.get("name")
    if name and not _is_placeholder_name(name):
        return name

    return name or f"Item #{defindex}"


def _is_warpaintable(schema_entry: Dict[str, Any]) -> bool:
    """Return True if ``schema_entry`` represents a weapon that can be warpainted."""

    if (
        schema_entry.get("craft_class") != "weapon"
        and schema_entry.get("craft_material_type") != "weapon"
    ):
        item_class = schema_entry.get("item_class", "")
        if not item_class.startswith("tf_weapon_"):
            return False

    name = schema_entry.get("item_name") or schema_entry.get("name") or ""
    if _is_placeholder_name(name):
        return False

    return True


WAR_PAINT_TOOL_DEFINDEXES = {5681, 5682, 5683}


def _has_attr(asset: dict, idx: int) -> bool:
    """Return True if ``asset`` contains an attribute with ``defindex`` ``idx``."""

    for attr in asset.get("attributes", []) or []:
        try:
            if int(attr.get("defindex")) == idx:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _extract_warpaint_tool_info(
    asset: dict,
) -> tuple[int | None, str | None, str | None, int | None, str | None]:
    """Return paintkit id, name, wear name, target weapon defindex and name."""

    paintkit_id = None
    wear_name = None
    target_def = None
    for attr in asset.get("attributes", []):
        try:
            idx = int(attr.get("defindex"))
        except (TypeError, ValueError):
            continue
        if idx == 134:
            raw = (
                attr.get("value")
                if attr.get("value") is not None
                else attr.get("float_value")
            )
            try:
                paintkit_id = int(float(raw)) if raw is not None else None
            except (TypeError, ValueError):
                continue
        elif idx == 725:
            raw = (
                attr.get("float_value")
                if attr.get("float_value") is not None
                else attr.get("value")
            )
            try:
                val = float(raw)
            except (TypeError, ValueError):
                continue
            if 0 <= val <= 1:
                name = local_data.WEAR_NAMES.get(str(int(val)))
                wear_name = name or _wear_tier(val)
        elif idx == 2014:
            raw = (
                attr.get("value")
                if attr.get("value") is not None
                else attr.get("float_value")
            )
            try:
                target_def = int(float(raw)) if raw is not None else None
            except (TypeError, ValueError):
                continue

    paintkit_name = None
    if paintkit_id is not None:
        paintkit_name = (
            local_data.PAINTKIT_NAMES_BY_ID.get(str(paintkit_id)) or "Unknown"
        )

    target_name = None
    if target_def is not None:
        target_entry = local_data.ITEMS_BY_DEFINDEX.get(target_def, {})
        target_name = _preferred_base_name(str(target_def), target_entry)

    return paintkit_id, paintkit_name, wear_name, target_def, target_name


def _is_warpaint_tool(schema_entry: Dict[str, Any]) -> bool:
    """Return True if ``schema_entry`` represents a warpaint tool."""

    if schema_entry.get("item_class") != "tool":
        return False

    tool = schema_entry.get("tool")
    if isinstance(tool, dict) and tool.get("type") == "paintkit":
        return True

    item_type = str(schema_entry.get("item_type_name", "")).lower()
    if "war paint" in item_type:
        return True

    name = str(schema_entry.get("item_name") or schema_entry.get("name") or "").lower()
    if "war paint" in name:
        return True

    return False


def _is_plain_craft_weapon(asset: dict, schema_entry: Dict[str, Any]) -> bool:
    """Return True if ``asset`` is a plain craft weapon without special attrs."""

    try:
        quality = int(asset.get("quality", 0))
    except (TypeError, ValueError):
        return False

    try:
        origin = int(asset.get("origin", -1))
    except (TypeError, ValueError):
        origin = -1
    if origin in CRAFT_WEAPON_ALLOWED_ORIGINS:
        return False

    if quality != 6:
        return False

    if (
        schema_entry.get("craft_class") != "weapon"
        and schema_entry.get("craft_material_type") != "weapon"
    ):
        return False

    if _extract_australium(asset):
        return False

    for attr in asset.get("attributes", []) or []:
        idx = attr.get("defindex")
        try:
            idx_int = int(idx)
        except (TypeError, ValueError):
            continue
        if idx_int in SPECIAL_SPELL_ATTRS:
            return False
        if idx_int in SPECIAL_KILLSTREAK_ATTRS:
            return False
        if idx_int in SPECIAL_FESTIVIZER_ATTRS:
            return False
        if idx_int in SPECIAL_PAINTKIT_ATTRS:
            return False

    if asset.get("custom_name") or asset.get("custom_desc"):
        return False

    return True


def _trade_hold_timestamp(asset: dict) -> int | None:
    """Return a trade hold expiry timestamp if present."""

    ts = asset.get("steam_market_tradeable_after") or asset.get(
        "steam_market_marketable_after"
    )
    try:
        if ts is not None:
            return int(ts)
    except (TypeError, ValueError):
        pass

    for desc in asset.get("descriptions", []):
        if not isinstance(desc, dict):
            continue
        app_data = desc.get("app_data")
        if not isinstance(app_data, dict):
            continue
        ts = app_data.get("steam_market_tradeable_after") or app_data.get(
            "steam_market_marketable_after"
        )
        try:
            if ts is not None:
                return int(ts)
        except (TypeError, ValueError):
            continue
    return None


def _has_trade_hold(asset: dict) -> bool:
    """Return ``True`` if the item has a temporary trade hold."""

    return _trade_hold_timestamp(asset) is not None


def _process_item(
    asset: dict,
    valuation_service: ValuationService | None = None,
) -> dict | None:
    """Return an enriched item dictionary for a single asset.

    Parameters
    ----------
    asset:
        Raw inventory item from Steam.
    valuation_service:
        Optional :class:`ValuationService` used to look up item values. When
        provided, price information is added under ``"price"`` and
        ``"price_string"`` keys. Defaults to
        :func:`~utils.valuation_service.get_valuation_service`, which returns a
        singleton service.
    """

    if valuation_service is None:
        valuation_service = get_valuation_service()

    origin_raw = asset.get("origin")
    tradable_raw = asset.get("tradable", 1)
    trade_hold_ts = _trade_hold_timestamp(asset)
    untradable_hold = False
    try:
        origin_int = int(origin_raw)
    except (TypeError, ValueError):
        origin_int = -1

    try:
        tradable_val = int(tradable_raw)
    except (TypeError, ValueError):  # pragma: no cover - fallback handling
        tradable_val = 1

    if asset.get("flag_cannot_trade"):
        if trade_hold_ts is not None:
            tradable_val = 1
            untradable_hold = True
        else:
            tradable_val = 0

    hide_item = tradable_val == 0
    if hide_item:
        valuation_service = None

    uncraftable = bool(asset.get("flag_cannot_craft"))

    defindex_raw = asset.get("defindex", 0)
    try:
        defindex_int = int(defindex_raw)
    except (TypeError, ValueError):
        logger.warning("Invalid defindex on asset: %r", defindex_raw)
        return None

    schema_entry = local_data.ITEMS_BY_DEFINDEX.get(defindex_int)
    if not schema_entry:
        logger.warning("Missing schema entry for defindex %s", defindex_int)
        schema_entry = {}

    if _is_plain_craft_weapon(asset, schema_entry):
        return None

    defindex = str(defindex_int)
    image_url = schema_entry.get("image_url", "")

    warpaintable = _is_warpaintable(schema_entry)
    warpaint_tool = defindex_int in WAR_PAINT_TOOL_DEFINDEXES or _is_warpaint_tool(
        schema_entry
    )

    paintkit_id = paintkit_name = None
    target_weapon_def = target_weapon_name = None
    wear_name = _extract_wear(asset)
    wear_float = _extract_wear_float(asset)

    if warpaint_tool:
        (
            paintkit_id,
            paintkit_name,
            wear_override,
            target_weapon_def,
            target_weapon_name,
        ) = _extract_warpaint_tool_info(asset)
        if paintkit_id is None:
            paintkit_id, paintkit_name = _extract_paintkit(asset, schema_entry)
        if wear_override:
            wear_name = wear_override
    elif warpaintable or not schema_entry:
        paintkit_id, paintkit_name = _extract_paintkit(asset, schema_entry)
        if paintkit_id is not None:
            warpaintable = True

    is_skin = bool(not warpaint_tool and schema_entry and _has_attr(asset, 834))

    base_weapon = _preferred_base_name(defindex, schema_entry)
    if not schema_entry:
        base_weapon = "Unknown Weapon"

    base_name = base_weapon
    skin_name = None
    composite_name = None
    resolved_name = base_name

    if warpaint_tool and paintkit_id is not None:
        suffix = f" ({wear_name})" if wear_name else ""
        resolved_name = f"War Paint: {paintkit_name}{suffix}"
    elif warpaintable and paintkit_id is not None:
        skin_name = paintkit_name
        composite_name = f"{paintkit_name} {base_weapon}"
        resolved_name = composite_name

    is_australium = asset.get("is_australium") or _extract_australium(asset)
    display_base = base_name
    if is_australium:
        clean_base = re.sub(
            r"^(Strange|Unique|Vintage|Haunted|Collector's|Genuine|Unusual)\s+",
            "",
            base_name,
            flags=re.IGNORECASE,
        )
        display_base = f"Australium {clean_base}"

    quality_id = asset.get("quality", 0)
    q_name = local_data.QUALITIES_BY_INDEX.get(quality_id)
    if not q_name:
        q_name = QUALITY_MAP.get(quality_id, ("Unknown",))[0]
    q_col = QUALITY_MAP.get(quality_id, ("", "#B2B2B2"))[1]
    name = _build_item_name(display_base, q_name, asset)

    ks_tier_val = _extract_killstreak_tier(asset)
    ks_tier, sheen_name, sheen_id = _extract_killstreak(asset)
    sheen_color = (
        KILLSTREAK_SHEEN_COLORS.get(sheen_id, (None, None))[1]
        if sheen_id is not None
        else None
    )
    ks_effect = _extract_killstreak_effect(asset)
    paint_name, paint_hex = _extract_paint(asset)
    pattern_seed = _extract_pattern_seed(asset)
    crate_series_name = _extract_crate_series(asset)
    spell_badges, spells = _extract_spells(asset)
    strange_parts = _extract_strange_parts(asset)
    kill_eater_counts, score_types = _extract_kill_eater_info(asset)

    badges: List[Dict[str, str]] = []

    # --- UNUSUAL EFFECT ----------------------------------------------------
    effect_info = _extract_unusual_effect(asset)
    if effect_info:
        effect_id = effect_info["id"]
        effect_name = effect_info["name"]
        effect = effect_info
    else:
        effect = None
        effect_id = effect_name = None

    if effect_id is not None:
        badges.append(
            {
                "icon": "★",
                "title": f"Unusual Effect: {effect_name or f'#{effect_id}'}",
                "color": "#8650AC",
                "label": effect_name or f"#{effect_id}",
                "type": "effect",
            }
        )
    # ----------------------------------------------------------------------

    display_name = (
        f"{display_base}"
        if effect_id is None
        else f"{effect_name or f'Effect #{effect_id}'} {display_base}"
    )
    original_name = name if effect_id is not None else None
    if effect_id is not None:
        name = display_name
    if ks_tier_val:
        tier_id = int(float(ks_tier_val))
        icon = KILLSTREAK_BADGE_ICONS.get(tier_id)
        if icon:
            title = KILLSTREAK_TIERS[tier_id]
            badges.append(
                {
                    "icon": icon,
                    "title": title,
                    "color": sheen_color or "#ff7e30",
                    "label": title,
                    "type": "killstreak",
                }
            )
    badges.extend(spell_badges)

    if paint_name:
        badges.append(
            {
                "icon": "\U0001f3a8",
                "title": f"Paint: {paint_name}",
                "label": paint_name,
                "type": "paint",
            }
        )
    if warpaintable and paintkit_id is not None:
        badges.append(
            {
                "icon": "\U0001f58c",
                "title": f"Warpaint: {paintkit_name}",
                "label": paintkit_name,
                "type": "warpaint",
            }
        )

    if warpaint_tool or (warpaintable and paintkit_id is not None):
        display_name = resolved_name

    item = {
        "id": asset.get("id"),
        "defindex": defindex,
        "name": name,
        "original_name": original_name,
        "base_name": base_name,
        "display_name": display_name,
        "is_australium": bool(is_australium),
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
        "origin": ORIGIN_MAP.get(origin_int),
        "custom_name": asset.get("custom_name"),
        "custom_description": asset.get("custom_desc"),
        "unusual_effect": effect,
        "unusual_effect_id": effect_id,
        "unusual_effect_name": effect_name,
        "killstreak_tier": ks_tier_val,
        "killstreak_name": KILLSTREAK_LABELS.get(ks_tier_val),
        "sheen": sheen_name,
        "sheen_name": sheen_name,
        "sheen_color": sheen_color,
        "paint_name": paint_name,
        "paint_hex": paint_hex,
        "wear_name": wear_name,
        "wear_float": wear_float,
        "pattern_seed": pattern_seed,
        "skin_name": skin_name,
        "composite_name": composite_name,
        "base_weapon": None if warpaint_tool else base_weapon if skin_name else None,
        "resolved_name": resolved_name,
        "warpaint_id": (
            paintkit_id
            if (warpaint_tool or warpaintable) and paintkit_id is not None
            else None
        ),
        "warpaint_name": (
            paintkit_name
            if (warpaint_tool or warpaintable) and paintkit_id is not None
            else None
        ),
        "paintkit_name": (
            paintkit_name
            if (warpaint_tool or warpaintable) and paintkit_id is not None
            else None
        ),
        "paintkit_id": paintkit_id,
        "target_weapon_defindex": target_weapon_def,
        "target_weapon_name": target_weapon_name,
        "is_war_paint_tool": warpaint_tool,
        "is_skin": is_skin,
        "crate_series_name": crate_series_name,
        "killstreak_effect": ks_effect,
        "spells": spells,
        "badges": badges,  # always present, may be empty
        "strange_parts": strange_parts,
        "strange_count": kill_eater_counts.get(1),
        "score_type": (
            _PARTS_BY_ID.get(score_types.get(1))
            or local_data.STRANGE_PART_NAMES.get(str(score_types.get(1)))
            if score_types.get(1) is not None
            else None
        ),
        "trade_hold_expires": trade_hold_ts,
        "untradable_hold": untradable_hold,
        "uncraftable": uncraftable,
        "_hidden": hide_item,
    }

    if valuation_service is not None:
        tradable = tradable_val

        if tradable:
            try:
                qid = int(quality_id)
            except (TypeError, ValueError):
                qid = 0
            try:
                formatted = valuation_service.format_price(
                    item.get("base_name", base_name),
                    qid,
                    bool(is_australium),
                    effect_id=effect_id,
                    killstreak_tier=ks_tier_val,
                    currencies=local_data.CURRENCIES,
                )
            except Exception:  # pragma: no cover - defensive fallback
                formatted = ""
            if formatted:
                item["price"] = valuation_service.get_price_info(
                    item.get("base_name", base_name),
                    qid,
                    bool(is_australium),
                    effect_id=effect_id,
                    killstreak_tier=ks_tier_val,
                )
                item["price_string"] = formatted
                item["formatted_price"] = formatted
            else:
                item["price"] = None
                item["price_string"] = ""
    return item


def enrich_inventory(
    data: Dict[str, Any],
    valuation_service: ValuationService | None = None,
) -> List[Dict[str, Any]]:
    """Return a list of inventory items enriched with schema info.

    Parameters
    ----------
    data:
        Inventory payload from Steam.
    valuation_service:
        Optional :class:`ValuationService` used to look up prices. Defaults to
        :func:`~utils.valuation_service.get_valuation_service`, which provides
        a singleton service.
    """
    if valuation_service is None:
        valuation_service = get_valuation_service()
    items_raw = data.get("items")
    if not isinstance(items_raw, list):
        return []

    items: List[Dict[str, Any]] = []

    for asset in items_raw:
        item = _process_item(asset, valuation_service)
        if not item:
            continue

        quality_flag = item.get("quality")
        if (
            quality_flag == 11
            or quality_flag == "Strange"
            or asset.get("quality") == 11
        ):
            attrs = item.get("attributes")
            if not isinstance(attrs, list):
                attrs = asset.get("attributes", [])
            parts_found: set[str] = set()
            for attr in attrs:
                if attr.get("defindex") == 214:
                    try:
                        idx = int(attr.get("value"))
                    except (TypeError, ValueError):
                        continue
                    name = _PARTS_BY_ID.get(idx)
                    if name:
                        parts_found.add(name)
            if parts_found:
                existing = item.get("strange_parts", [])
                if not isinstance(existing, list):
                    existing = []
                all_parts = set(existing) | parts_found
                item["strange_parts"] = sorted(all_parts)

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


def process_inventory(
    data: Dict[str, Any],
    valuation_service: ValuationService | None = None,
) -> List[Dict[str, Any]]:
    """Return enriched items sorted by descending price."""
    if valuation_service is None:
        valuation_service = get_valuation_service()
    items = enrich_inventory(data, valuation_service)

    def _sort_key(item: Dict[str, Any]) -> tuple[float, str]:
        price_info = item.get("price") or {}
        value = price_info.get("value_raw", 0) or 0
        return -float(value), item["name"]

    return sorted(items, key=_sort_key)


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

    local_data.load_files(verbose=True)
    with file_path.open() as f:
        raw = json.load(f)

    items = process_inventory(raw)
    print(json.dumps(items, indent=2))


if __name__ == "__main__":  # pragma: no cover - manual debug helper
    run_enrichment_test()
