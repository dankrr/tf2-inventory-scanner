from typing import Dict, Any

from .. import local_data
from ..constants import SPELL_MAP
from .extractors_misc import _extract_australium
from .extract_attr_classes import get_attr_ids

_exclusions = local_data.load_exclusions()
CRAFT_WEAPON_ALLOWED_ORIGINS = set(_exclusions.get("craft_weapon_exclusions", []))

SPECIAL_SPELL_ATTRS: set[int] = set(SPELL_MAP.keys()) | set(range(8900, 8926))
_ids = get_attr_ids()
SPECIAL_KILLSTREAK_ATTRS: set[int] = {
    i for i in (
        _ids.get("killstreakEffect"),
        _ids.get("killstreakSheen"),
        _ids.get("killstreakTier"),
    )
    if i is not None
}
SPECIAL_FESTIVIZER_ATTRS: set[int] = {
    i for i in (_ids.get("festive"),) if i is not None
}
SPECIAL_PAINTKIT_ATTRS: set[int] = {
    i
    for i in (
        _ids.get("paintkit"),
        _ids.get("patternSeedLo"),
        _ids.get("patternSeedHi"),
        *(_ids.get("wear", set())),
    )
    if i is not None
}


def _has_attr(asset: dict, idx: int) -> bool:
    """Return True if ``asset`` contains an attribute with ``defindex`` ``idx``."""

    for attr in asset.get("attributes", []) or []:
        try:
            if int(attr.get("defindex")) == idx:
                return True
        except (TypeError, ValueError):
            continue
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


__all__ = [
    "_is_plain_craft_weapon",
    "_has_attr",
    "CRAFT_WEAPON_ALLOWED_ORIGINS",
    "SPECIAL_SPELL_ATTRS",
    "SPECIAL_KILLSTREAK_ATTRS",
    "SPECIAL_FESTIVIZER_ATTRS",
    "SPECIAL_PAINTKIT_ATTRS",
]
