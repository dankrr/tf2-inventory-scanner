"""Translate and enrich TF2 inventory data."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List
import struct
import argparse
import json

from utils.constants import (
    KILLSTREAK_EFFECTS,
    KILLSTREAK_TIERS,
    SHEEN_NAMES,
    KILLSTREAK_BADGE_ICONS,
)


QUALITY_MAP = {
    0: "Normal",
    1: "Genuine",
    3: "Vintage",
    5: "Unusual",
    6: "Unique",
    7: "Community",
    8: "Valve",
    9: "Self-Made",
    10: "Customized",
    11: "Strange",
    13: "Haunted",
    14: "Collector's",
    15: "Decorated Weapon",
}


def _index_descriptions(descriptions: Iterable[dict]) -> Dict[tuple[str, str], dict]:
    """Return mapping of ``(classid, instanceid)`` to description dict."""
    mapping: Dict[tuple[str, str], dict] = {}
    for desc in descriptions:
        classid = str(desc.get("classid", ""))
        inst = str(desc.get("instanceid", "0"))
        mapping[(classid, inst)] = desc
    return mapping


def _attr_value(attrs: Iterable[dict], idx: int) -> Any | None:
    for attr in attrs:
        if int(attr.get("defindex", -1)) == idx:
            if "float_value" in attr:
                return attr.get("float_value")
            return attr.get("value")
    return None


def _wear_tier(value: float) -> str:
    """Return human readable wear tier for a 0-1 float."""
    if value < 0.07:
        return "Factory New"
    if value < 0.15:
        return "Minimal Wear"
    if value < 0.38:
        return "Field-Tested"
    if value < 0.45:
        return "Well-Worn"
    return "Battle Scarred"


def _decode_seed_info(attrs: Iterable[dict]) -> tuple[float | None, int | None]:
    """Return ``(wear_float, pattern_seed)`` from custom paintkit seed attrs."""

    lo = hi = None
    for attr in attrs:
        idx = int(attr.get("defindex", -1))
        if idx == 866:
            lo = int(attr.get("value") or 0)
        elif idx == 867:
            hi = int(attr.get("value") or 0)
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


def _collect_unmapped(attrs: Iterable[dict], known: Iterable[int]) -> dict:
    remaining: dict[str, Any] = {}
    for attr in attrs:
        idx = int(attr.get("defindex", -1))
        if idx not in known:
            remaining[str(idx)] = attr.get("float_value") or attr.get("value")
    return remaining


def enrich_inventory(
    raw_inventory: dict,
    schema: dict,
    items_game: dict,
    maps: Dict[str, Dict[str, str]],
) -> List[dict]:
    """Return a list of enriched inventory items."""

    desc_map = _index_descriptions(raw_inventory.get("descriptions", []))
    result: List[dict] = []

    for asset in raw_inventory.get("assets", []):
        key = (str(asset.get("classid")), str(asset.get("instanceid", "0")))
        desc = desc_map.get(key, {})
        app_data = desc.get("app_data", {})
        attrs = asset.get("attributes") or app_data.get("attributes") or []

        defindex = str(app_data.get("def_index") or asset.get("defindex") or "0")
        schema_entry = schema.get(defindex, {})
        ig_entry = items_game.get(defindex, {})

        base_name = (
            ig_entry.get("name")
            or schema_entry.get("item_name")
            or desc.get("market_hash_name")
            or f"Item {defindex}"
        )
        quality_id = int(asset.get("quality") or app_data.get("quality") or 6)
        quality_name = QUALITY_MAP.get(quality_id, "Unknown")

        image_url = schema_entry.get("image_url") or desc.get("icon_url")

        effect_id = int(asset.get("effect") or _attr_value(attrs, 134) or 0)
        effect_names = maps.get("effect_names", {})
        effect_name = effect_names.get(str(effect_id)) if effect_id else None

        ks_tier_val = _attr_value(attrs, 2025)
        ks_tier = None
        if ks_tier_val is not None:
            kst = (
                int(float(ks_tier_val))
                if isinstance(ks_tier_val, str)
                else int(ks_tier_val)
            )
            ks_tier = maps.get("killstreak_names", {}).get(
                str(kst)
            ) or KILLSTREAK_TIERS.get(kst)

        sheen_val = _attr_value(attrs, 2014)
        sheen = None
        if sheen_val is not None:
            sv = int(float(sheen_val)) if isinstance(sheen_val, str) else int(sheen_val)
            sheen = maps.get("killstreak_names", {}).get(str(sv)) or SHEEN_NAMES.get(sv)

        ks_eff_val = _attr_value(attrs, 2013)
        ks_effect = None
        if ks_eff_val is not None:
            ksv = (
                int(float(ks_eff_val))
                if isinstance(ks_eff_val, str)
                else int(ks_eff_val)
            )
            ks_effect = maps.get("killstreak_names", {}).get(
                str(ksv)
            ) or KILLSTREAK_EFFECTS.get(ksv)

        paint_id = _attr_value(attrs, 142) or _attr_value(attrs, 261)
        paint_name = None
        if paint_id is not None:
            paint_name = maps.get("paint_names", {}).get(str(int(paint_id)))

        wear_val = _attr_value(attrs, 725)
        wear_name = _wear_tier(float(wear_val)) if wear_val is not None else None
        wear_float, pattern_seed = _decode_seed_info(attrs)
        if wear_val is None and wear_float is not None:
            wear_name = _wear_tier(wear_float)

        paintkit_val = _attr_value(attrs, 834)
        paintkit_name = None
        if paintkit_val is not None:
            paintkit_name = maps.get("paintkit_names", {}).get(str(int(paintkit_val)))

        crate_id = int(_attr_value(attrs, 187) or 0)
        crate_name = (
            maps.get("crate_series_names", {}).get(str(crate_id)) if crate_id else None
        )

        parts: list[str] = []
        for attr in attrs:
            pid = int(attr.get("defindex", 0))
            name = maps.get("strange_part_names", {}).get(str(pid))
            if name and name not in parts:
                parts.append(name)

        badges: set[str] = set()
        if effect_name:
            badges.add("🔥")
        if paint_name:
            badges.update(["🎨", "🖌"])
        if paintkit_name or wear_name:
            badges.add("🎨")
        if ks_tier_val is not None:
            tier_id = int(float(ks_tier_val))
            badge_icon = KILLSTREAK_BADGE_ICONS.get(tier_id)
            if badge_icon:
                badges.add(badge_icon)
        if quality_id == 11 or parts:
            badges.add("🧠")

        item = {
            "name": base_name,
            "image_url": image_url,
            "defindex": int(defindex) if defindex.isdigit() else defindex,
            "quality": quality_name,
            "tradable": bool(desc.get("tradable", 0)),
            "marketable": bool(desc.get("marketable", 0)),
            "unusual_effect": effect_name,
            "killstreak_tier": ks_tier,
            "sheen": sheen,
            "killstreaker": ks_effect,
            "paint": paint_name,
            "wear": wear_name,
            "paintkit": paintkit_name,
            "pattern_seed": pattern_seed,
            "crate_series": crate_name,
            "strange_parts": parts,
            "badges": list(badges),
            "raw_attributes": _collect_unmapped(
                attrs, [134, 142, 261, 725, 834, 2025, 2014, 2013, 187, 866, 867]
            ),
        }
        result.append(item)

    result.sort(key=lambda x: x["name"])
    return result


def _load_json(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Translate and enrich TF2 inventory data"
    )
    parser.add_argument("--inv", required=True, help="Inventory JSON file")
    parser.add_argument("--schema", required=True, help="TF2 schema JSON")
    parser.add_argument("--items-game", required=True, help="items_game cleaned JSON")
    parser.add_argument("--maps", required=True, help="Folder containing mapping files")
    args = parser.parse_args()

    raw_inventory = _load_json(Path(args.inv))
    schema = _load_json(Path(args.schema))
    items_game = _load_json(Path(args.items_game))

    maps = {}
    for p in Path(args.maps).glob("*.json"):
        maps[p.stem] = _load_json(p)

    items = enrich_inventory(raw_inventory, schema, items_game, maps)
    print(json.dumps(items[:2], indent=2))


if __name__ == "__main__":
    main()

    sample = {
        "assets": [
            {
                "classid": "1",
                "instanceid": "0",
                "attributes": [{"defindex": 134, "float_value": 15}],
            }
        ],
        "descriptions": [
            {
                "classid": "1",
                "instanceid": "0",
                "app_data": {"def_index": "1"},
                "tradable": 1,
                "marketable": 1,
            }
        ],
    }
    maps = {"effect_names": {"15": "Burning Flames"}}
    enriched = enrich_inventory(
        sample,
        {"1": {"item_name": "Test Item"}},
        {"1": {"name": "Test Item"}},
        maps,
    )
    assert enriched[0]["unusual_effect"] == "Burning Flames"
