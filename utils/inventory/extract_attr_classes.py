from typing import Any

from .. import local_data

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


def refresh_attr_classes() -> None:
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


refresh_attr_classes()


def get_attr_class(idx: Any) -> str | None:
    """Return the attribute class string for ``idx`` using the cached schema."""

    try:
        idx_int = int(idx)
    except (TypeError, ValueError):
        return None
    info = local_data.SCHEMA_ATTRIBUTES.get(idx_int)
    if isinstance(info, dict):
        return info.get("attribute_class")
    return None


__all__ = [
    "refresh_attr_classes",
    "get_attr_class",
    "UNUSUAL_CLASSES",
    "KILLSTREAK_TIER_CLASSES",
    "KILLSTREAK_SHEEN_CLASSES",
    "KILLSTREAK_EFFECT_CLASSES",
    "PAINT_CLASSES",
    "WEAR_CLASSES",
    "PATTERN_SEED_LO_CLASSES",
    "PATTERN_SEED_HI_CLASSES",
    "PAINTKIT_CLASSES",
    "CRATE_SERIES_CLASSES",
]
