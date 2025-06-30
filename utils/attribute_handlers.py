import logging
from typing import Any, Dict

from . import schema_cache as sc

logger = logging.getLogger(__name__)

_KILLSTREAK_TIER = {1: "Killstreak", 2: "Specialized", 3: "Professional"}


def handle_custom_name(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    name = attr.get("value") or attr.get("string_value")
    if name:
        item["custom_name"] = str(name)


def handle_paint_color(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    pid = int(attr.get("float_value", 0))
    paint = sc.get_paint(pid)
    if paint:
        item["paint_name"] = paint.get("name")
        item["paint_hex"] = paint.get("hex")


def handle_spell_bitmask(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    bitmask = int(attr.get("float_value", 0))
    for bit, name in sc._SPELLS.items():
        if bitmask & bit:
            item.setdefault("spells", []).append(name)
            flag = name.lower().replace(" ", "_")
            item.setdefault("spell_flags", {})[flag] = True


def handle_killstreak_tier(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    tier = int(attr.get("float_value", 0))
    item["killstreak_tier"] = _KILLSTREAK_TIER.get(tier)


def handle_sheen(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    name = sc.get_sheen(int(attr.get("float_value", 0)))
    if name:
        item["sheen"] = name


def handle_killstreaker(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    name = sc.get_killstreaker(int(attr.get("float_value", 0)))
    if name:
        item["killstreaker"] = name


def handle_strange_part(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    name = sc.get_strange_part(attr.get("defindex"))
    if name:
        item.setdefault("strange_parts", []).append(name)


def handle_festivized(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    item["is_festivized"] = bool(int(attr.get("float_value", 0)))


def handle_unusual_effect(item: Dict[str, Any], attr: Dict[str, Any]) -> None:
    name = sc.get_effect(int(attr.get("float_value", 0)))
    if name:
        item["unusual_effect"] = name


ATTRIBUTE_HANDLERS = {
    134: handle_custom_name,
    142: handle_paint_color,
    730: handle_spell_bitmask,
    2025: handle_killstreak_tier,
    2013: handle_sheen,
    2071: handle_killstreaker,
    380: handle_strange_part,
    381: handle_strange_part,
    382: handle_strange_part,
    383: handle_strange_part,
    384: handle_strange_part,
    385: handle_strange_part,
    2041: handle_festivized,
    2042: handle_festivized,
    2043: handle_festivized,
    2044: handle_festivized,
    214: handle_unusual_effect,
}

__all__ = [
    "ATTRIBUTE_HANDLERS",
    "handle_custom_name",
    "handle_paint_color",
    "handle_spell_bitmask",
    "handle_killstreak_tier",
    "handle_sheen",
    "handle_killstreaker",
    "handle_strange_part",
    "handle_festivized",
    "handle_unusual_effect",
]
