from __future__ import annotations

import json
import logging
import re
from html import unescape
from pathlib import Path
from typing import Any, Dict, List, Tuple

from . import steam_api_client, schema_cache
from .attribute_handlers import ATTRIBUTE_HANDLERS

logger = logging.getLogger(__name__)

MAPPING_FILE = Path(__file__).with_name("warpaint_mapping.json")
WARPAINT_MAP: Dict[str, str] = {}
if MAPPING_FILE.exists():
    with MAPPING_FILE.open() as f:
        WARPAINT_MAP = json.load(f)


def _decode_attributes(asset: Dict[str, Any], item: Dict[str, Any]) -> None:
    for attr in asset.get("attributes", []):
        defindex = attr.get("defindex")
        handler = ATTRIBUTE_HANDLERS.get(defindex)
        if handler:
            handler(item, attr)
        else:
            item.setdefault("misc_attrs", []).append(attr)


def _legacy_spells(asset: Dict[str, Any], item: Dict[str, Any]) -> None:
    lines: List[str] = []
    flags = {
        "exorcism": False,
        "paint_spell": False,
        "footprints": False,
        "pumpkin_bombs": False,
        "voices_from_below": False,
    }
    for desc in asset.get("descriptions", []):
        if not isinstance(desc, dict):
            continue
        text = unescape(desc.get("value", ""))
        text = re.sub(r"<[^>]+>", "", text).strip()
        ltext = text.lower()
        if "halloween" in ltext or "spell" in ltext:
            lines.append(text)
        if "exorcism" in ltext:
            flags["exorcism"] = True
        if "paint" in ltext and "spell" in ltext:
            flags["paint_spell"] = True
        if "footprints" in ltext:
            flags["footprints"] = True
        if "pumpkin" in ltext:
            flags["pumpkin_bombs"] = True
        if "voices" in ltext or "rare spell" in ltext:
            flags["voices_from_below"] = True
    if lines:
        item["spells"] = lines
    if any(flags.values()):
        item.setdefault("spell_flags", {}).update(flags)


def _extract_unusual_effect(asset: Dict[str, Any]) -> str | None:
    if "effect" in asset:
        name = schema_cache.get_effect(int(asset["effect"]))
        if name:
            return name
    for desc in asset.get("descriptions", []):
        if not isinstance(desc, dict):
            continue
        text = unescape(desc.get("value", ""))
        text = re.sub(r"<[^>]+>", "", text)
        match = re.search(r"Unusual Effect:\s*(.+)", text, re.I)
        if match:
            return match.group(1).strip()
    return None


def _build_display_name(quality: str, item: Dict[str, Any]) -> str:
    base = item.get("custom_name") or item.get("base_name", "")
    parts: List[str] = []
    if item.get("killstreak_tier"):
        parts.append(item["killstreak_tier"])
    if item.get("unusual_effect"):
        parts.append(item["unusual_effect"])
        if quality not in ("Unique", "Normal", "Unusual"):
            parts.append(quality)
    else:
        if quality not in ("Unique", "Normal"):
            parts.append(quality)
    parts.append(base)
    if item.get("sheen"):
        parts.append(f"({item['sheen']})")
    return " ".join(parts)


def generate_badges(item: Dict[str, Any]) -> List[Dict[str, str]]:
    flags = item.get("spell_flags", {})
    badges: List[Dict[str, str]] = []
    if item.get("paint_name"):
        badges.append({"icon": "🎨", "title": f"Painted: {item['paint_name']}"})
    if item.get("killstreak_tier"):
        badges.append({"icon": "⚔️", "title": item["killstreak_tier"]})
    if item.get("killstreaker"):
        badges.append({"icon": "💀", "title": item["killstreaker"]})
    if item.get("sheen"):
        badges.append({"icon": "✨", "title": f"Sheen: {item['sheen']}"})
    if flags.get("footprints"):
        badges.append({"icon": "👣", "title": "Footprints spell"})
    if flags.get("exorcism"):
        badges.append({"icon": "👻", "title": "Exorcism"})
    if flags.get("pumpkin_bombs"):
        badges.append({"icon": "🎃", "title": "Pumpkin Bombs"})
    if flags.get("voices_from_below"):
        badges.append({"icon": "🗣", "title": "Voices From Below"})
    if item.get("strange_parts"):
        badges.append({"icon": "📊", "title": "Strange Parts"})
    if item.get("is_festivized"):
        badges.append({"icon": "🎄", "title": "Festivized"})
    if item.get("unusual_effect"):
        badges.append({"icon": "🔥", "title": f"Unusual: {item['unusual_effect']}"})
    return badges


def fetch_inventory(steam_id: str) -> Tuple[Dict[str, Any], str]:
    status, data = steam_api_client.fetch_inventory(steam_id)
    if status not in ("parsed", "incomplete"):
        data = {"items": []}
    else:
        data = data or {"items": []}
    return data, status


def enrich_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    items_raw = data.get("items")
    if not isinstance(items_raw, list):
        return []

    items: List[Dict[str, Any]] = []
    for asset in items_raw:
        defindex = int(asset.get("defindex", 0))
        try:
            schema_item = schema_cache.get_item(defindex)
        except KeyError:
            logger.warning("Unknown defindex %s", defindex)
            continue

        qid = int(asset.get("quality", 0))
        q_lookup = schema_cache.get_quality(qid)
        if q_lookup:
            quality_name, q_color = q_lookup
        else:
            quality_name, q_color = ("Normal" if qid == 0 else "Unknown", "#B2B2B2")

        origin = schema_cache.get_origin(int(asset.get("origin", 0)))

        item: Dict[str, Any] = {
            "defindex": str(defindex),
            "quality": quality_name,
            "quality_color": q_color or "#B2B2B2",
            "image_url": schema_item.get("image_url", ""),
            "item_type_name": schema_item.get("item_type_name"),
            "item_name": schema_item.get("item_name"),
            "craft_class": schema_item.get("craft_class"),
            "craft_material_type": schema_item.get("craft_material_type"),
            "item_set": schema_item.get("item_set"),
            "capabilities": schema_item.get("capabilities"),
            "tags": schema_item.get("tags"),
            "equip_regions": schema_item.get("equip_regions"),
            "item_class": schema_item.get("item_class"),
            "slot_type": schema_item.get("slot_type"),
            "level": asset.get("level"),
            "origin": origin,
            "base_name": WARPAINT_MAP.get(str(defindex))
            or schema_item.get("base_name")
            or schema_item.get("item_name"),
        }

        _decode_attributes(asset, item)

        if not item.get("spells"):
            _legacy_spells(asset, item)
        if not item.get("unusual_effect"):
            ue = _extract_unusual_effect(asset)
            if ue:
                item["unusual_effect"] = ue

        item["name"] = _build_display_name(quality_name, item)
        badges = generate_badges(item)
        if badges:
            item["badges"] = badges
        items.append(item)

    return items


def process_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = enrich_inventory(data)
    return sorted(items, key=lambda i: i["name"])
