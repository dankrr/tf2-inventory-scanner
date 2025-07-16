from typing import Any, Dict, List, Optional

from .constants import SHEEN_NAMES, KILLSTREAK_EFFECTS

# Defindexes for killstreak kits and fabricators
KIT_DEFINDEXES = {
    6527,  # Basic Killstreak Kit
    6523,  # Specialized Killstreak Kit
    6526,  # Professional Killstreak Kit
}

FABRICATOR_DEFINDEXES = {
    20002,  # Specialized Fabricator
    20003,  # Professional Fabricator
}

_TIER_LABELS = {
    6527: "Basic Killstreak Kit",
    6523: "Specialized Killstreak Kit",
    6526: "Professional Killstreak Kit",
    20002: "Specialized Fabricator",
    20003: "Professional Fabricator",
}


def _lookup_name(
    defindex: int, names: Optional[Dict[str, str]], items: Optional[Dict[int, Any]]
) -> str:
    """Return an item name from defindex lookup tables."""

    if names and str(defindex) in names:
        return names[str(defindex)]
    if items and defindex in items and isinstance(items[defindex], dict):
        return (
            items[defindex].get("item_name") or items[defindex].get("name") or "Unknown"
        )
    return "Unknown"


def _parse_kit(
    asset: Dict[str, Any],
    names: Optional[Dict[str, str]],
    items: Optional[Dict[int, Any]],
) -> Dict[str, Any]:
    """Parse a Killstreak Kit item."""

    weapon_id = None
    sheen_id = None
    ks_id = None
    for attr in asset.get("attributes", []):
        idx = attr.get("defindex")
        if idx == 2012:
            weapon_id = int(attr.get("float_value", 0))
        elif idx == 2014:
            sheen_id = int(attr.get("float_value", 0))
        elif idx == 2013:
            ks_id = int(attr.get("float_value", 0))
    weapon_name = _lookup_name(weapon_id or 0, names, items)
    sheen = SHEEN_NAMES.get(sheen_id)
    killstreaker = KILLSTREAK_EFFECTS.get(ks_id)
    tier_name = _TIER_LABELS.get(asset.get("defindex"))
    description_parts = [tier_name or "Killstreak Kit", "for", weapon_name]
    extras: List[str] = []
    if sheen:
        extras.append(f"Sheen: {sheen}")
    if killstreaker:
        extras.append(f"Killstreaker: {killstreaker}")
    if extras:
        description_parts.append(f"({', '.join(extras)})")
    description = " ".join(description_parts)
    return {
        "id": asset.get("id"),
        "type": "Kit",
        "tier": tier_name,
        "weapon_name": weapon_name,
        "sheen": sheen,
        "killstreaker": killstreaker,
        "description": description,
    }


def _parse_fabricator(
    asset: Dict[str, Any],
    names: Optional[Dict[str, str]],
    items: Optional[Dict[int, Any]],
) -> Dict[str, Any]:
    """Parse a Fabricator item."""

    output = None
    requirements = []
    for attr in asset.get("attributes", []):
        if attr.get("is_output"):
            output = attr
        else:
            part_id = attr.get("itemdef")
            qty = attr.get("quantity", 1)
            part_name = _lookup_name(part_id, names, items)
            requirements.append({"part": part_name, "qty": qty})
    weapon_id = None
    sheen_id = None
    ks_id = None
    tier_name = None
    if output:
        kit_def = output.get("itemdef")
        tier_name = _TIER_LABELS.get(kit_def)
        for sub in output.get("attributes", []):
            idx = sub.get("defindex")
            if idx == 2012:
                weapon_id = int(sub.get("float_value", 0))
            elif idx == 2014:
                sheen_id = int(sub.get("float_value", 0))
            elif idx == 2013:
                ks_id = int(sub.get("float_value", 0))
    weapon_name = _lookup_name(weapon_id or 0, names, items)
    sheen = SHEEN_NAMES.get(sheen_id)
    killstreaker = KILLSTREAK_EFFECTS.get(ks_id)
    description = f"Fabricator → Will create {tier_name} for {weapon_name}"
    if sheen or killstreaker:
        extra = ", ".join(
            [
                f"Sheen: {sheen}" if sheen else None,
                f"Killstreaker: {killstreaker}" if killstreaker else None,
            ]
        )
        extra = extra.replace("None, ", "").replace(", None", "")
        description += f" ({extra})"
    return {
        "id": asset.get("id"),
        "type": "Fabricator",
        "tier": tier_name,
        "weapon_name": weapon_name,
        "sheen": sheen,
        "killstreaker": killstreaker,
        "requirements": requirements,
        "description": description,
    }


def parse_killstreak_item(
    asset: Dict[str, Any],
    *,
    defindex_names: Optional[Dict[str, str]] = None,
    items: Optional[Dict[int, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Return parsed info for killstreak kits or fabricators."""

    d = asset.get("defindex")
    if d in KIT_DEFINDEXES:
        return _parse_kit(asset, defindex_names, items)
    if d in FABRICATOR_DEFINDEXES:
        return _parse_fabricator(asset, defindex_names, items)
    return None
