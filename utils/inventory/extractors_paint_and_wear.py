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
)

logger = logging.getLogger(__name__)


def _extract_paint(asset: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """Return paint name and hex color if present."""

    refresh_attr_classes()
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


def _extract_econ_tag(
    asset: Dict[str, Any], *, category: str, category_name: str | None = None
) -> str | None:
    """Return localized Steam Econ tag value for a category if present."""

    tags = asset.get("tags")
    if not isinstance(tags, list):
        return None
    category = category.lower()
    category_name = category_name.lower() if category_name else None
    for tag in tags:
        if not isinstance(tag, dict):
            continue
        tag_category = str(tag.get("category", "")).lower()
        tag_category_name = str(tag.get("category_name", "")).lower()
        if tag_category != category and (
            category_name is None or tag_category_name != category_name
        ):
            continue
        raw = (
            tag.get("localized_tag_name")
            or tag.get("name")
            or tag.get("internal_name")
        )
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def _extract_wear_attr_value(asset: Dict[str, Any]) -> tuple[float | None, Any | None]:
    """Return ``(wear_float, raw_value)`` when a wear attribute can be parsed."""

    refresh_attr_classes()
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = get_attr_class(idx)
        if attr_class not in WEAR_CLASSES and idx not in (725, 749):
            continue
        raw = attr.get("float_value")
        if raw is None:
            raw = attr.get("value")
        try:
            val = float(raw)
        except (TypeError, ValueError):
            logger.warning("Invalid wear value: %r", raw)
            continue
        if not 0 <= val <= 1 and val not in (0, 1, 2, 3, 4):
            logger.warning("Wear value out of range: %s", val)
        return val, raw

    wear_float, _ = _decode_seed_info(asset.get("attributes", []))
    if wear_float is not None:
        return wear_float, wear_float
    return None, None


def _is_schema_wear_id_value(wear_float: float, wear_raw: Any) -> bool:
    """Return True when wear metadata is encoded as an integer schema ID."""

    if wear_float not in (0, 1, 2, 3, 4):
        return False

    # Steam can serialize true boundary floats as float values like ``1.0``.
    # Treat explicit floats as float-based wear, not schema IDs.
    if isinstance(wear_raw, float):
        return False

    if isinstance(wear_raw, int):
        return True

    if isinstance(wear_raw, str):
        raw = wear_raw.strip()
        if not raw:
            return False
        if raw in {"0", "1", "2", "3", "4"}:
            return True
        return False

    return False


def resolve_wear(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve wear metadata using econ tag, schema map, then float fallback."""

    econ_wear = _extract_econ_tag(asset, category="Exterior")
    if econ_wear:
        wear_float, wear_raw = _extract_wear_attr_value(asset)
        if wear_float is not None and not (0 <= wear_float <= 1):
            wear_float = None
        return {
            "wear": econ_wear,
            "wear_name": econ_wear,
            "exterior": econ_wear,
            "wear_float": wear_float,
            "wear_raw": wear_raw,
            "wear_source": "econ_tag",
        }

    wear_float, wear_raw = _extract_wear_attr_value(asset)
    if wear_float is not None:
        if _is_schema_wear_id_value(wear_float, wear_raw):
            mapped = local_data.WEAR_NAMES_BY_ID.get(int(wear_float))
            if mapped:
                return {
                    "wear": mapped,
                    "wear_name": mapped,
                    "exterior": mapped,
                    "wear_float": None,
                    "wear_raw": wear_raw,
                    "wear_source": "schema_wears",
                }

        if 0 <= wear_float <= 1:
            # Prefer canonical schema names when they include this float tier.
            fallback_name = _wear_tier(wear_float)
            mapped = next(
                (
                    schema_name
                    for schema_name in local_data.WEAR_NAMES_BY_ID.values()
                    if str(schema_name).lower() == fallback_name.lower()
                ),
                None,
            )
            if mapped:
                return {
                    "wear": mapped,
                    "wear_name": mapped,
                    "exterior": mapped,
                    "wear_float": wear_float,
                    "wear_raw": wear_raw,
                    "wear_source": "schema_wears",
                }

            return {
                "wear": fallback_name,
                "wear_name": fallback_name,
                "exterior": fallback_name,
                "wear_float": wear_float,
                "wear_raw": wear_raw,
                "wear_source": "float",
            }

    return {
        "wear": None,
        "wear_name": None,
        "exterior": None,
        "wear_float": None,
        "wear_raw": wear_raw,
        "wear_source": "none",
    }


def _extract_wear(asset: Dict[str, Any]) -> str | None:
    """Backward-compatible wear extractor returning only the wear name."""

    return resolve_wear(asset).get("wear_name")


def _extract_wear_float(asset: Dict[str, Any]) -> float | None:
    """Backward-compatible helper returning normalized wear float when available."""

    return resolve_wear(asset).get("wear_float")


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
    paintkit_id = None
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = get_attr_class(idx)
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
            attr_class = get_attr_class(idx)
            if idx == 834 or attr_class in PAINTKIT_CLASSES:
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

    # Legacy fallback: some payloads expose paintkit ids under defindex 749.
    # Reject fractional wear floats (e.g. 0.04) so wear data is not misread as
    # a paintkit id.
    for attr in asset.get("attributes", []):
        if attr.get("defindex") != 749:
            continue
        raw = attr.get("value")
        if raw is None:
            raw = attr.get("float_value")
        try:
            raw_float = float(raw) if raw is not None else None
        except (TypeError, ValueError):
            logger.warning("Invalid paintkit id: %r", raw)
            continue
        if raw_float is None or not raw_float.is_integer() or raw_float <= 0:
            continue
        paintkit_id = int(raw_float)
        if paintkit_id is not None:
            logger.warning("Using numeric fallback for paintkit index %s", 749)
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
    "resolve_wear",
]
