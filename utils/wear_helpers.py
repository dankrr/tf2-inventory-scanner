import struct
from typing import Iterable, Tuple

from . import local_data


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


def wear_tier_from_float(value: float) -> int:
    """Return a numeric wear tier for ``value`` between 0 and 1."""

    if value < 0.07:
        return 0
    if value < 0.15:
        return 1
    if value < 0.38:
        return 2
    if value < 0.45:
        return 3
    return 4


def _decode_seed_info(attrs: Iterable[dict]) -> Tuple[float | None, int | None]:
    """Return ``(wear_float, pattern_seed)`` from custom paintkit seed attrs."""

    mapping = local_data.SCHEMA_ATTRIBUTES or {}

    def get_class(idx: int | None) -> str | None:
        try:
            key = int(idx) if idx is not None else None
        except (TypeError, ValueError):
            return None
        info = mapping.get(key)
        if isinstance(info, dict):
            return info.get("attribute_class")
        return None

    lo_class = get_class(866)
    hi_class = get_class(867)

    lo = hi = None
    for attr in attrs:
        idx = attr.get("defindex")
        attr_class = get_class(idx)
        if (lo_class and attr_class == lo_class) or idx == 866:
            try:
                lo = int(attr.get("value") or 0)
            except (TypeError, ValueError):
                continue
        elif (hi_class and attr_class == hi_class) or idx == 867:
            try:
                hi = int(attr.get("value") or 0)
            except (TypeError, ValueError):
                continue
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
