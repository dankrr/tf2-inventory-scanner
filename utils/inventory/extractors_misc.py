from typing import Any, Dict, Tuple, List
import logging
import json
from pathlib import Path
from .. import local_data
from ..constants import SPELL_MAP
from .extract_attr_classes import (
    refresh_attr_classes,
    get_attr_class,
    CRATE_SERIES_CLASSES,
)

logger = logging.getLogger(__name__)

SCHEMA_DIR = Path("cache/schema")
try:  # graceful fallback if the optional file is missing
    with open(SCHEMA_DIR / "strange_parts.json") as fp:
        _PARTS_BY_ID = {int(v[2:]): k for k, v in json.load(fp).items()}
except FileNotFoundError:  # pragma: no cover - only used in dev/test
    _PARTS_BY_ID = {}


def _extract_crate_series(asset: Dict[str, Any]) -> str | None:
    """Return crate series name if present."""

    refresh_attr_classes()
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = get_attr_class(idx)
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
    if "voices from below" in lname:
        return "🗣️"
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


__all__ = [
    "_PARTS_BY_ID",
    "_extract_crate_series",
    "_extract_australium",
    "_extract_spells",
    "_spell_icon",
    "_extract_strange_parts",
    "_extract_kill_eater_info",
    "_trade_hold_timestamp",
    "_has_trade_hold",
]
