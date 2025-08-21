"""Helpers for resolving attribute classes and defindex IDs.

The module exposes two layers of schema-driven helpers:

``refresh_attr_classes``
    Populates sets of attribute *classes* for quick membership checks.

``get_attr_ids``
    Lazily resolves well-known attribute *defindexes* by name and caches them
    in :data:`ATTR_IDS`. These defindexes are resolved from
    :data:`utils.local_data.SCHEMA_ATTRIBUTES` and avoid any hard-coded
    numbers.
"""

from typing import Any, Dict, Set, TypedDict

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


class AttrIds(TypedDict):
    """Typed mapping of schema attribute names to defindexes."""

    killstreakTier: int | None
    killstreakSheen: int | None
    killstreakEffect: int | None
    paint: Set[int]
    wear: Set[int]
    patternSeedLo: int | None
    patternSeedHi: int | None
    paintkit: int | None
    crateSeries: int | None
    strange: int | None
    festive: int | None
    canApplyStrange: int | None
    unusual: Set[int]
    marketable: int | None
    uncraftable: int | None
    qualityElevated: int | None
    inventoryOffers: int | None


# Cache of resolved attribute defindexes
ATTR_IDS: AttrIds = AttrIds(
    killstreakTier=None,
    killstreakSheen=None,
    killstreakEffect=None,
    paint=set(),
    wear=set(),
    patternSeedLo=None,
    patternSeedHi=None,
    paintkit=None,
    crateSeries=None,
    strange=None,
    festive=None,
    canApplyStrange=None,
    unusual=set(),
    marketable=None,
    uncraftable=None,
    qualityElevated=None,
    inventoryOffers=None,
)


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

    _resolve_attr_ids(mapping)

    ids = ATTR_IDS

    UNUSUAL_CLASSES = {cls(i) for i in ids["unusual"]} - {None}
    KILLSTREAK_TIER_CLASSES = (
        {cls(ids["killstreakTier"])} - {None} if ids["killstreakTier"] is not None else set()
    )
    KILLSTREAK_SHEEN_CLASSES = (
        {cls(ids["killstreakSheen"])} - {None} if ids["killstreakSheen"] is not None else set()
    )
    KILLSTREAK_EFFECT_CLASSES = (
        {cls(ids["killstreakEffect"])} - {None} if ids["killstreakEffect"] is not None else set()
    )
    PAINT_CLASSES = {cls(i) for i in ids["paint"]} - {None}
    WEAR_CLASSES = {cls(i) for i in ids["wear"]} - {None}
    PATTERN_SEED_LO_CLASSES = (
        {cls(ids["patternSeedLo"])} - {None} if ids["patternSeedLo"] is not None else set()
    )
    PATTERN_SEED_HI_CLASSES = (
        {cls(ids["patternSeedHi"])} - {None} if ids["patternSeedHi"] is not None else set()
    )
    PAINTKIT_CLASSES = (
        {cls(ids["paintkit"])} - {None} if ids["paintkit"] is not None else set()
    )
    CRATE_SERIES_CLASSES = (
        {cls(ids["crateSeries"])} - {None} if ids["crateSeries"] is not None else set()
    )


def _resolve_attr_ids(mapping: Dict[int, Dict[str, Any]]) -> None:
    """Populate :data:`ATTR_IDS` from ``mapping``."""

    def find(name: str) -> int | None:
        for idx, info in mapping.items():
            if info.get("name") == name:
                return int(idx)
        return None

    ATTR_IDS.update(
        killstreakTier=find("killstreak tier"),
        killstreakSheen=find("killstreak idleeffect"),
        killstreakEffect=find("killstreak effect"),
        paint={i for i in (find("set item tint RGB"), find("set item tint RGB 2")) if i is not None},
        wear={i for i in (find("set_item_texture_wear"), find("texture_wear_default")) if i is not None},
        patternSeedLo=find("custom_paintkit_seed_lo"),
        patternSeedHi=find("custom_paintkit_seed_hi"),
        paintkit=find("paintkit_proto_def_index"),
        crateSeries=find("set supply crate series"),
        strange=find("kill eater"),
        festive=find("is_festivized"),
        canApplyStrange=find("can apply strange"),
        unusual={i for i in (find("attach particle effect"), find("taunt attach particle index")) if i is not None},
        marketable=find("is marketable"),
        uncraftable=find("never craftable"),
        qualityElevated=find("elevate quality"),
        inventoryOffers=find("allow_halloween_offering"),
    )


def get_attr_ids() -> AttrIds:
    """Return cached attribute defindexes, resolving on first use."""

    if not any(ATTR_IDS.values()):
        refresh_attr_classes()
    return ATTR_IDS


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
    "get_attr_ids",
    "ATTR_IDS",
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
