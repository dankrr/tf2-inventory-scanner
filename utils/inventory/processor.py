from typing import Dict, List
import logging
import re

from .. import local_data
from ..schema_provider import is_festivized
from ..valuation_service import ValuationService, get_valuation_service
from ..constants import (
    KILLSTREAK_TIERS,
    KILLSTREAK_LABELS,
    ORIGIN_MAP,
    KILLSTREAK_BADGE_ICONS,
)
from .maps_and_constants import (
    QUALITY_MAP,
    STRANGE_QUALITY_ID,
    WAR_PAINT_TOOL_DEFINDEXES,
)
from .extractors_unusual_killstreak import (
    _extract_unusual_effect,
    _extract_killstreak_tier,
    _extract_killstreak,
    _extract_killstreak_effect,
    _compute_sheen_colors,
)
from .extractors_paint_and_wear import (
    _extract_paint,
    _extract_wear,
    _extract_wear_float,
    _extract_pattern_seed,
    _extract_paintkit,
)
from .extractors_misc import (
    _extract_crate_series,
    _extract_australium,
    _extract_spells,
    _extract_strange_parts,
    _extract_kill_eater_info,
    _trade_hold_timestamp,
    _PARTS_BY_ID,
)
from .tools_and_kits import (
    _is_warpaint_tool,
    _extract_warpaint_tool_info,
    _extract_killstreak_tool_info,
)
from .naming_and_warpaint import (
    _is_warpaintable,
    _preferred_base_name,
    _build_item_name,
)
from .filters_and_rules import _is_plain_craft_weapon, _has_attr

logger = logging.getLogger(__name__)


def _process_item(
    asset: dict,
    valuation_service: ValuationService | None = None,
) -> dict | None:
    """Return an enriched item dictionary for a single asset.

    Parameters
    ----------
    asset:
        Raw inventory item from Steam.
    valuation_service:
        Optional :class:`ValuationService` used to look up item values. When
        provided, price information is added under ``"price"`` and
        ``"price_string"`` keys. Defaults to
        :func:`~utils.valuation_service.get_valuation_service`, which returns a
        singleton service.
    """

    if valuation_service is None:
        valuation_service = get_valuation_service()

    attrs = asset.get("attributes", [])

    origin_raw = asset.get("origin")
    tradable_raw = asset.get("tradable", 1)
    trade_hold_ts = _trade_hold_timestamp(asset)
    untradable_hold = False
    try:
        origin_int = int(origin_raw)
    except (TypeError, ValueError):
        origin_int = -1

    try:
        tradable_val = int(tradable_raw)
    except (TypeError, ValueError):  # pragma: no cover - fallback handling
        tradable_val = 1

    if asset.get("flag_cannot_trade"):
        if trade_hold_ts is not None:
            tradable_val = 1
            untradable_hold = True
        else:
            tradable_val = 0

    hide_item = tradable_val == 0
    if hide_item:
        valuation_service = None

    uncraftable = bool(asset.get("flag_cannot_craft"))
    craftable = not uncraftable

    defindex_raw = asset.get("defindex", 0)
    try:
        defindex_int = int(defindex_raw)
    except (TypeError, ValueError):
        logger.warning("Invalid defindex on asset: %r", defindex_raw)
        return None

    schema_entry = local_data.ITEMS_BY_DEFINDEX.get(defindex_int)
    if not schema_entry:
        logger.warning("Missing schema entry for defindex %s", defindex_int)
        schema_entry = {}

    if _is_plain_craft_weapon(asset, schema_entry):
        return None

    defindex = str(defindex_int)
    image_url = schema_entry.get("image_url", "")

    warpaintable = _is_warpaintable(schema_entry)
    warpaint_tool = defindex_int in WAR_PAINT_TOOL_DEFINDEXES or _is_warpaint_tool(
        schema_entry
    )

    paintkit_id = paintkit_name = None
    target_weapon_def = target_weapon_name = None
    wear_name = _extract_wear(asset)
    wear_float = _extract_wear_float(asset)

    if warpaint_tool:
        (
            paintkit_id,
            paintkit_name,
            wear_override,
            target_weapon_def,
            target_weapon_name,
        ) = _extract_warpaint_tool_info(asset)
        if paintkit_id is None:
            paintkit_id, paintkit_name = _extract_paintkit(asset, schema_entry)
        if wear_override:
            wear_name = wear_override
    elif warpaintable or not schema_entry:
        paintkit_id, paintkit_name = _extract_paintkit(asset, schema_entry)
        if paintkit_id is not None:
            warpaintable = True

    is_skin = bool(not warpaint_tool and schema_entry and _has_attr(asset, 834))

    base_weapon = _preferred_base_name(defindex, schema_entry)
    if not schema_entry:
        base_weapon = "Unknown Weapon"

    base_name = base_weapon
    skin_name = None
    composite_name = None
    resolved_name = base_name

    if warpaint_tool and paintkit_id is not None:
        suffix = f" ({wear_name})" if wear_name else ""
        resolved_name = f"War Paint: {paintkit_name}{suffix}"
    elif warpaintable and paintkit_id is not None:
        skin_name = paintkit_name
        composite_name = f"{paintkit_name} {base_weapon}"
        resolved_name = composite_name

    is_australium = asset.get("is_australium") or _extract_australium(asset)
    display_base = base_name
    if is_australium:
        clean_base = re.sub(
            r"^(Strange|Unique|Vintage|Haunted|Collector's|Genuine|Unusual)\s+",
            "",
            base_name,
            flags=re.IGNORECASE,
        )
        display_base = f"Australium {clean_base}"

    quality_id = asset.get("quality", 0)
    q_name = local_data.QUALITIES_BY_INDEX.get(quality_id)
    if not q_name:
        q_name = QUALITY_MAP.get(quality_id, ("Unknown",))[0]
    q_col = QUALITY_MAP.get(quality_id, ("", "#B2B2B2"))[1]
    name = _build_item_name(display_base, q_name, asset)

    ks_tier_val = _extract_killstreak_tier(asset)
    ks_tier, sheen_name, sheen_id = _extract_killstreak(asset)

    sheen_colors = _compute_sheen_colors(sheen_id)
    sheen_color = sheen_colors[0] if sheen_colors else None
    ks_effect = _extract_killstreak_effect(asset)
    paint_name, paint_hex = _extract_paint(asset)
    pattern_seed = _extract_pattern_seed(asset)
    crate_series_name = _extract_crate_series(asset)
    spell_badges, spells = _extract_spells(asset)
    strange_parts = _extract_strange_parts(asset)
    kill_eater_counts, score_types = _extract_kill_eater_info(asset)

    has_strange_tracking = kill_eater_counts.get(1) is not None

    if has_strange_tracking:
        border_color = QUALITY_MAP[STRANGE_QUALITY_ID][1]
    else:
        border_color = q_col

    ks_tool_info = _extract_killstreak_tool_info(asset)
    include_stack_key = False
    stack_key = None
    if ks_tool_info:
        include_stack_key = True
        if target_weapon_def is None:
            target_weapon_def = ks_tool_info["weapon_defindex"]
            target_weapon_name = ks_tool_info["weapon_name"]
        if ks_tier_val is None:
            ks_tier_val = ks_tool_info["tier_id"]
        if sheen_name is None:
            sheen_name = ks_tool_info["sheen_name"]
            sheen_id = ks_tool_info["sheen_id"]
            colors = _compute_sheen_colors(sheen_id)
            if colors:
                sheen_colors = colors
                sheen_color = sheen_colors[0]
        if ks_effect is None:
            ks_effect = ks_tool_info["killstreaker_name"]

    sheen_gradient_css = (
        f"background: linear-gradient(90deg, {sheen_colors[0]} 50%, {sheen_colors[1]} 50%)"
        if len(sheen_colors) > 1
        else None
    )

    badges: List[Dict[str, str]] = []

    # --- UNUSUAL EFFECT ----------------------------------------------------
    effect_info = _extract_unusual_effect(asset)
    if effect_info:
        effect_id = effect_info["id"]
        effect_name = effect_info["name"]
        effect = effect_info
    else:
        effect = None
        effect_id = effect_name = None

    if effect_id is not None:
        badges.append(
            {
                "icon": "★",
                "title": f"Unusual Effect: {effect_name or f'#{effect_id}'}",
                "color": "#8650AC",
                "label": effect_name or f"#{effect_id}",
                "type": "effect",
            }
        )
    # ----------------------------------------------------------------------

    display_name = (
        f"{display_base}"
        if effect_id is None
        else f"{effect_name or f'Effect #{effect_id}'} {display_base}"
    )
    original_name = name if effect_id is not None else None
    if effect_id is not None:
        name = display_name
    if ks_tier_val:
        tier_id = int(float(ks_tier_val))
        icon = KILLSTREAK_BADGE_ICONS.get(tier_id)
        if icon:
            title = KILLSTREAK_TIERS[tier_id]
            badges.append(
                {
                    "icon": icon,
                    "title": title,
                    "color": sheen_color or "#ff7e30",
                    "label": title,
                    "type": "killstreak",
                }
            )
    badges.extend(spell_badges)

    if paint_name:
        badges.append(
            {
                "icon": "\U0001f3a8",
                "title": f"Paint: {paint_name}",
                "label": paint_name,
                "type": "paint",
            }
        )
    if warpaintable and paintkit_id is not None:
        warpaint_icon = local_data.ITEMS_BY_DEFINDEX.get(5813, {}).get("image_url")
        badges.append(
            {
                "icon_url": warpaint_icon,
                "title": f"Warpaint: {paintkit_name}",
                "label": paintkit_name,
                "type": "warpaint",
            }
        )

    if warpaint_tool or (warpaintable and paintkit_id is not None):
        display_name = resolved_name

    has_statclock = has_strange_tracking and quality_id == 15
    stat_clock_img = None
    if has_statclock:
        if warpaint_tool:
            display_name = f"{display_name} (StatTrak\u2122)"
        else:
            display_name = f"{display_name} (Strange)"
        stat_clock_img = (
            "http://media.steampowered.com/apps/440/icons/"
            "stattrack.fea7f754b9ab447df18af382036d7d93ed97aca9.png"
        )
        if stat_clock_img:
            badges.insert(
                0,
                {
                    "icon_url": stat_clock_img,
                    "type": "statclock",
                    "title": "StatTrak\u2122",
                },
            )

    item = {
        "id": asset.get("id"),
        "defindex": defindex,
        "name": name,
        "original_name": original_name,
        "base_name": base_name,
        "display_name": display_name,
        "attributes": attrs,
        "is_festivized": bool(is_festivized(attrs)),
        "is_australium": bool(is_australium),
        "quality": q_name,
        "quality_color": q_col,
        "border_color": border_color,
        "image_url": image_url,
        "item_type_name": schema_entry.get("item_type_name"),
        "item_name": schema_entry.get("name"),
        "craft_class": schema_entry.get("craft_class"),
        "craft_material_type": schema_entry.get("craft_material_type"),
        "item_set": schema_entry.get("item_set"),
        "capabilities": schema_entry.get("capabilities"),
        "tags": schema_entry.get("tags"),
        "equip_regions": schema_entry.get("equip_regions")
        or schema_entry.get("equip_region"),
        "item_class": schema_entry.get("item_class"),
        "slot_type": schema_entry.get("item_slot") or schema_entry.get("slot_type"),
        "level": asset.get("level"),
        "origin": ORIGIN_MAP.get(origin_int),
        "custom_name": asset.get("custom_name"),
        "custom_description": asset.get("custom_desc"),
        "unusual_effect": effect,
        "unusual_effect_id": effect_id,
        "unusual_effect_name": effect_name,
        "killstreak_tier": ks_tier_val,
        "killstreak_name": KILLSTREAK_LABELS.get(ks_tier_val),
        "tier_name": (
            ks_tool_info.get("tier_name")
            if ks_tool_info
            else KILLSTREAK_TIERS.get(int(float(ks_tier_val))) if ks_tier_val else None
        ),
        "sheen": sheen_name,
        "sheen_name": sheen_name,
        "sheen_color": sheen_color,
        "sheen_colors": sheen_colors,
        "sheen_gradient_css": sheen_gradient_css,
        "paint_name": paint_name,
        "paint_hex": paint_hex,
        "wear_name": wear_name,
        "wear_float": wear_float,
        "pattern_seed": pattern_seed,
        "skin_name": skin_name,
        "composite_name": composite_name,
        "base_weapon": None if warpaint_tool else base_weapon if skin_name else None,
        "resolved_name": resolved_name,
        "warpaint_id": (
            paintkit_id
            if (warpaint_tool or warpaintable) and paintkit_id is not None
            else None
        ),
        "warpaint_name": (
            paintkit_name
            if (warpaint_tool or warpaintable) and paintkit_id is not None
            else None
        ),
        "paintkit_name": (
            paintkit_name
            if (warpaint_tool or warpaintable) and paintkit_id is not None
            else None
        ),
        "paintkit_id": paintkit_id,
        "target_weapon_defindex": target_weapon_def,
        "target_weapon_name": target_weapon_name,
        "target_weapon_image": (
            local_data.ITEMS_BY_DEFINDEX.get(target_weapon_def or 0, {}).get(
                "image_url"
            )
            if target_weapon_def is not None
            else None
        ),
        "is_war_paint_tool": warpaint_tool,
        "is_skin": is_skin,
        "killstreak_tool_type": ks_tool_info.get("tool_type") if ks_tool_info else None,
        "fabricator_requirements": (
            ks_tool_info.get("requirements") if ks_tool_info else None
        ),
        "stack_key": stack_key if include_stack_key else None,
        "crate_series_name": crate_series_name,
        "killstreak_effect": ks_effect,
        "spells": spells,
        "badges": badges,  # always present, may be empty
        "has_strange_tracking": has_strange_tracking,
        "statclock_badge": stat_clock_img,
        "strange_parts": strange_parts,
        "strange_count": kill_eater_counts.get(1),
        "score_type": (
            _PARTS_BY_ID.get(score_types.get(1))
            or local_data.STRANGE_PART_NAMES.get(str(score_types.get(1)))
            if score_types.get(1) is not None
            else None
        ),
        "trade_hold_expires": trade_hold_ts,
        "untradable_hold": untradable_hold,
        "uncraftable": uncraftable,
        "craftable": craftable,
        "_hidden": hide_item,
    }

    if valuation_service is not None:
        tradable = tradable_val

        if tradable:
            try:
                qid = int(quality_id)
            except (TypeError, ValueError):
                qid = 0
            try:
                formatted = valuation_service.format_price(
                    item.get("base_name", base_name),
                    qid,
                    craftable,
                    bool(is_australium),
                    effect_id=effect_id,
                    killstreak_tier=ks_tier_val,
                    currencies=local_data.CURRENCIES,
                )
            except Exception:  # pragma: no cover - defensive fallback
                formatted = ""
            if formatted:
                item["price"] = valuation_service.get_price_info(
                    item.get("base_name", base_name),
                    qid,
                    craftable,
                    bool(is_australium),
                    effect_id=effect_id,
                    killstreak_tier=ks_tier_val,
                )
                item["price_string"] = formatted
                item["formatted_price"] = formatted
            else:
                item["price"] = None
                item["price_string"] = ""
    return item


__all__ = ["_process_item"]
