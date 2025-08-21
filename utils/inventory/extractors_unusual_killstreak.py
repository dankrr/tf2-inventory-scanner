from typing import Any, Dict, Tuple
import logging
import re
from html import unescape

from .. import local_data
from ..constants import (
    KILLSTREAK_TIERS,
    SHEEN_NAMES,
    KILLSTREAK_SHEEN_COLORS,
    KILLSTREAK_EFFECTS,
)
from .extract_attr_classes import (
    refresh_attr_classes,
    get_attr_class,
    KILLSTREAK_TIER_CLASSES,
    KILLSTREAK_SHEEN_CLASSES,
    KILLSTREAK_EFFECT_CLASSES,
)

logger = logging.getLogger(__name__)

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

    refresh_attr_classes()
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = get_attr_class(idx)
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

    refresh_attr_classes()
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
        attr_class = get_attr_class(idx)
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


def _extract_killstreak_effect(asset: Dict[str, Any]) -> str | None:
    """Return killstreak effect string if present."""

    refresh_attr_classes()
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        attr_class = get_attr_class(idx)
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


def _compute_sheen_colors(sheen_id: int | None) -> list[str]:
    """Return list of colors for given sheen_id. Handles Team Shine as two-color gradient."""

    if sheen_id is None:
        return []
    if sheen_id == 1:  # Team Shine
        return ["#cc3434", "#5885a2"]  # Red and Blue
    color = KILLSTREAK_SHEEN_COLORS.get(sheen_id, (None, None))[1]
    return [color] if color else []


__all__ = [
    "_extract_unusual_effect",
    "_extract_killstreak_tier",
    "_extract_killstreak",
    "_extract_killstreak_effect",
    "_compute_sheen_colors",
    "EFFECTS_MAP",
]
