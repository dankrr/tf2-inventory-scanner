from typing import Dict, Any
import logging

from .. import local_data
from ..constants import KILLSTREAK_TIERS, SHEEN_NAMES, KILLSTREAK_EFFECTS
from ..wear_helpers import _wear_tier
from .maps_and_constants import (
    KILLSTREAK_KIT_DEFINDEXES,
    KILLSTREAK_FABRICATOR_DEFINDEXES,
    FABRICATOR_PART_IDS,
)
from .naming_and_warpaint import _preferred_base_name

logger = logging.getLogger(__name__)


def _is_warpaint_tool(schema_entry: Dict[str, Any]) -> bool:
    """Return True if ``schema_entry`` represents a warpaint tool."""

    if schema_entry.get("item_class") != "tool":
        return False

    tool = schema_entry.get("tool")
    if isinstance(tool, dict) and tool.get("type") == "paintkit":
        return True

    item_type = str(schema_entry.get("item_type_name", "")).lower()
    if "war paint" in item_type:
        return True

    name = str(schema_entry.get("item_name") or schema_entry.get("name") or "").lower()
    if "war paint" in name:
        return True

    return False


def _extract_warpaint_tool_info(
    asset: dict,
) -> tuple[int | None, str | None, str | None, int | None, str | None]:
    """Return paintkit id, name, wear name, target weapon defindex and name."""

    paintkit_id = None
    wear_name = None
    target_def = None
    for attr in asset.get("attributes", []):
        try:
            idx = int(attr.get("defindex"))
        except (TypeError, ValueError):
            continue
        if idx == 134:
            raw = (
                attr.get("value")
                if attr.get("value") is not None
                else attr.get("float_value")
            )
            try:
                paintkit_id = int(float(raw)) if raw is not None else None
            except (TypeError, ValueError):
                continue
        elif idx == 725:
            raw = (
                attr.get("float_value")
                if attr.get("float_value") is not None
                else attr.get("value")
            )
            try:
                val = float(raw)
            except (TypeError, ValueError):
                continue
            if 0 <= val <= 1:
                name = local_data.WEAR_NAMES.get(str(int(val)))
                wear_name = name or _wear_tier(val)
        elif idx == 2014:
            raw = (
                attr.get("value")
                if attr.get("value") is not None
                else attr.get("float_value")
            )
            try:
                target_def = int(float(raw)) if raw is not None else None
            except (TypeError, ValueError):
                continue

    paintkit_name = None
    if paintkit_id is not None:
        paintkit_name = (
            local_data.PAINTKIT_NAMES_BY_ID.get(str(paintkit_id)) or "Unknown"
        )

    target_name = None
    if target_def is not None:
        target_entry = local_data.ITEMS_BY_DEFINDEX.get(target_def, {})
        target_name = _preferred_base_name(str(target_def), target_entry)

    return paintkit_id, paintkit_name, wear_name, target_def, target_name


def _extract_killstreak_tool_info(asset: dict) -> dict | None:
    """Return parsed info for killstreak kits and fabricators."""

    try:
        defindex = int(asset.get("defindex"))
    except (TypeError, ValueError):
        return None

    if defindex not in KILLSTREAK_KIT_DEFINDEXES | KILLSTREAK_FABRICATOR_DEFINDEXES:
        return None

    is_fabricator = defindex in KILLSTREAK_FABRICATOR_DEFINDEXES
    attrs = []
    requirements: list[dict] | None = None
    if is_fabricator:
        for entry in asset.get("attributes", []):
            if entry.get("is_output"):
                attrs = entry.get("attributes") or []
            else:
                itemdef_raw = entry.get("itemdef")
                try:
                    itemdef = int(itemdef_raw)
                except (TypeError, ValueError):
                    continue
                if itemdef in FABRICATOR_PART_IDS:
                    qty_raw = entry.get("quantity")
                    try:
                        qty = int(qty_raw) if qty_raw is not None else 0
                    except (TypeError, ValueError):
                        qty = 0
                    part_entry = local_data.ITEMS_BY_DEFINDEX.get(itemdef, {})
                    part_name = (
                        part_entry.get("item_name")
                        or part_entry.get("name")
                        or f"#{itemdef}"
                    )
                    if requirements is None:
                        requirements = []
                    requirements.append({"part": part_name, "qty": qty})
    else:
        attrs = asset.get("attributes", [])

    weapon_def = None
    sheen_id = None
    effect_id = None
    tier_id = None
    for attr in attrs:
        idx = attr.get("defindex")
        raw = attr.get("float_value") if "float_value" in attr else attr.get("value")
        try:
            val = int(float(raw)) if raw is not None else None
        except (TypeError, ValueError):
            continue
        if idx == 2012:
            weapon_def = val
        elif idx == 2014:
            sheen_id = val
        elif idx == 2013:
            effect_id = val
        elif idx == 2025:
            tier_id = val

    weapon_name = None
    weapon_image = None
    if weapon_def is not None:
        weapon_entry = local_data.ITEMS_BY_DEFINDEX.get(weapon_def, {})
        weapon_name = _preferred_base_name(str(weapon_def), weapon_entry)
        weapon_image = weapon_entry.get("image_url")

    sheen_name = SHEEN_NAMES.get(sheen_id)
    if sheen_id is not None and sheen_name is None:
        logger.warning("Unknown sheen id: %s", sheen_id)
    effect_name = local_data.KILLSTREAK_EFFECT_NAMES.get(
        str(effect_id)
    ) or KILLSTREAK_EFFECTS.get(effect_id)
    tier_name = KILLSTREAK_TIERS.get(tier_id)

    return {
        "tool_type": "fabricator" if is_fabricator else "kit",
        "tier_id": tier_id,
        "tier_name": tier_name,
        "weapon_defindex": weapon_def,
        "weapon_name": weapon_name,
        "weapon_image": weapon_image,
        "sheen_id": sheen_id,
        "sheen_name": sheen_name,
        "killstreaker_id": effect_id,
        "killstreaker_name": effect_name,
        "requirements": requirements,
    }


__all__ = [
    "_is_warpaint_tool",
    "_extract_warpaint_tool_info",
    "_extract_killstreak_tool_info",
]
