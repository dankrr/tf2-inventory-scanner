from typing import Any, Dict, Tuple
import logging
import re

from .. import local_data
from ..constants import PAINT_COLORS
from ..helpers import best_match_from_keys
from ..wear_helpers import _decode_seed_info
from .extract_attr_classes import (
    refresh_attr_classes,
    get_attr_class,
    PAINT_CLASSES,
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


def _extract_wear_attr_value(
    asset: Dict[str, Any]
) -> tuple[float | None, Any | None, int | None]:
    """Return ``(wear_raw_float, wear_raw, source_attr)`` from canonical TF2 wear data.

    TF2 decorated exterior metadata is canonically stored on attribute defindex ``725``
    (``set_item_texture_wear``). This helper intentionally ignores unrelated numeric
    attributes so gameplay counters or paintkit values cannot be misinterpreted as wear.
    """

    refresh_attr_classes()
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = get_attr_class(idx)
        if idx != 725 and attr_class != "set_item_texture_wear":
            continue
        raw = attr.get("float_value")
        if raw is None:
            raw = attr.get("value")
        try:
            val = float(raw)
        except (TypeError, ValueError):
            logger.warning("Invalid canonical wear value: %r", raw)
            return None, raw, 725
        return val, raw, 725

    return None, None, None


def _wear_name_from_id(wear_id: int) -> str | None:
    """Resolve canonical wear label from cached schema wear IDs."""

    if wear_id < 1 or wear_id > 5:
        return None
    mapping = local_data.WEAR_NAMES_BY_ID
    return mapping.get(wear_id) or mapping.get(str(wear_id))


def _decode_texture_wear(wear_raw_float: float | None) -> tuple[int | None, str | None]:
    """Decode TF2 texture wear float to ``(wear_id, wear_name)``.

    Canonical mapping uses ``round(wear_raw_float * 5)`` and accepts only IDs 1..5.
    """

    if wear_raw_float is None:
        return None, None
    wear_id = round(wear_raw_float * 5)
    if wear_id < 1 or wear_id > 5:
        return None, None
    return wear_id, _wear_name_from_id(wear_id)


def resolve_wear(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve TF2 exterior metadata using econ tags and canonical wear attribute 725."""

    wear_raw_float, wear_raw, wear_source_attr = _extract_wear_attr_value(asset)
    wear_id, mapped_name = _decode_texture_wear(wear_raw_float)
    econ_wear = _extract_econ_tag(asset, category="Exterior")

    wear_name = econ_wear or mapped_name
    wear_source = "econ_tag" if econ_wear else "schema_wears" if wear_name else "none"
    wear_float = wear_raw_float if wear_name is not None else None

    return {
        "wear": wear_name,
        "wear_name": wear_name,
        "exterior": wear_name,
        "wear_float": wear_float,
        "wear_raw": wear_raw,
        "wear_raw_float": wear_raw_float if wear_name is not None else None,
        "wear_id": wear_id if wear_name is not None else None,
        "wear_source_attr": wear_source_attr if wear_name is not None else None,
        "wear_source": wear_source,
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
