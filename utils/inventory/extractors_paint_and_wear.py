from typing import Any, Dict, Tuple
import logging
import re

from .. import local_data
from ..constants import PAINT_COLORS
from ..helpers import best_match_from_keys
from ..wear_helpers import _wear_tier, _decode_seed_info
from .extract_attr_classes import (
    refresh_attr_classes,
    get_attr_class,
    PAINT_CLASSES,
    WEAR_CLASSES,
    PAINTKIT_CLASSES,
    get_attr_ids,
)

logger = logging.getLogger(__name__)


def _extract_paint(asset: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """Return paint name and hex color if present."""

    refresh_attr_classes()
    ids = get_attr_ids()
    paint_idxs = ids.get("paint", set())

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = get_attr_class(idx)
        if attr_class in PAINT_CLASSES:
            val = int(attr.get("float_value", 0))
            name = local_data.PAINT_NAMES.get(str(val))
            hex_color = PAINT_COLORS.get(val, (None, None))[1]
            if not name:
                name = PAINT_COLORS.get(val, (None, None))[0]
            if hex_color and not re.match(r"^#[0-9A-Fa-f]{6}$", hex_color):
                hex_color = None
            return name, hex_color
        elif idx in paint_idxs:
            logger.warning("Using fallback for paint index %s", idx)
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

    refresh_attr_classes()
    ids = get_attr_ids()
    wear_idxs = ids.get("wear", set())

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = get_attr_class(idx)
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
        elif idx in wear_idxs:
            logger.warning("Using fallback for wear index %s", idx)
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

    refresh_attr_classes()
    ids = get_attr_ids()
    wear_idxs = ids.get("wear", set())

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = get_attr_class(idx)
        if attr_class in WEAR_CLASSES or idx in wear_idxs:
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

    refresh_attr_classes()
    ids = get_attr_ids()
    pk_idx = ids.get("paintkit")
    paintkit_id = None

    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = get_attr_class(idx)
        if (pk_idx is not None and idx == pk_idx) or attr_class in PAINTKIT_CLASSES:
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
                if pk_idx is not None and idx == pk_idx and attr_class not in PAINTKIT_CLASSES:
                    logger.warning("Using fallback for paintkit index %s", idx)
                name = local_data.PAINTKIT_NAMES_BY_ID.get(str(paintkit_id))
                return paintkit_id, (name or "Unknown")

    if paintkit_id is None:
        for attr in asset.get("attributes", []):
            idx = attr.get("defindex")
            attr_class = get_attr_class(idx)
            if (pk_idx is not None and idx == pk_idx) or attr_class in PAINTKIT_CLASSES:
                raw = attr.get("float_value")
                try:
                    paintkit_id = int(float(raw)) if raw is not None else None
                except (TypeError, ValueError):
                    logger.warning("Invalid paintkit id: %r", raw)
                    continue
                if paintkit_id is not None:
                    logger.warning("Using fallback for paintkit index %s", idx)
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


__all__ = [
    "_extract_paint",
    "_extract_wear",
    "_extract_wear_float",
    "_extract_pattern_seed",
    "_slug_to_paintkit_name",
    "_extract_paintkit",
]
