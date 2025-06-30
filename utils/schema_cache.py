import json
import logging
from pathlib import Path
from typing import Any, Dict, Tuple

import vdf

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = BASE_DIR / "cache"

_CLOUD = "https://steamcommunity-a.akamaihd.net/economy/image/"

_ITEMS: Dict[int, Dict[str, Any]] = {}
_QUALITIES: Dict[int, Tuple[str, str | None]] = {}
_ORIGINS: Dict[int, str] = {}
_PAINTS: Dict[int, Dict[str, str | None]] = {}
_EFFECTS: Dict[int, str] = {}
_SHEENS: Dict[int, str] = {}
_KILLSTREAKERS: Dict[int, str] = {}
_STRANGE_PARTS: Dict[int, str] = {}
_SPELLS: Dict[int, str] = {}


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def _load_schema_items() -> None:
    path = CACHE_DIR / "schema_items.json"
    if not path.exists():
        logger.warning("Missing %s", path)
        return
    try:
        data = _load_json(path)
    except Exception as exc:  # pragma: no cover - corrupted file
        logger.warning("Failed reading %s: %s", path, exc)
        return
    items = (data.get("result") or data).get("items", [])
    for entry in items:
        try:
            idx = int(entry.get("defindex"))
        except Exception:
            continue
        img = (
            entry.get("image_url_large")
            or entry.get("image_url")
            or entry.get("icon_url_large")
            or entry.get("icon_url")
            or ""
        )
        if img and not img.startswith("http"):
            img = f"{_CLOUD}{img}/360fx360f"
        _ITEMS[idx] = {
            "defindex": idx,
            "base_name": entry.get("item_name") or entry.get("name"),
            "image_url": img,
            "item_type_name": entry.get("item_type_name"),
            "item_name": entry.get("name"),
            "craft_class": entry.get("craft_class"),
            "craft_material_type": entry.get("craft_material_type"),
            "item_set": entry.get("item_set"),
            "capabilities": entry.get("capabilities"),
            "tags": entry.get("tags"),
            "equip_regions": entry.get("equip_regions"),
            "item_class": entry.get("item_class"),
            "slot_type": entry.get("item_slot"),
        }


def _load_schema_overview() -> None:
    path = CACHE_DIR / "schema_overview.json"
    if not path.exists():
        logger.warning("Missing %s", path)
        return
    try:
        data = _load_json(path)
    except Exception as exc:  # pragma: no cover - corrupted file
        logger.warning("Failed reading %s: %s", path, exc)
        return
    res = data.get("result", data)
    q_colors = res.get("quality_colors", {})
    q_names = res.get("qualityNames", {})
    for name, qid in res.get("qualities", {}).items():
        qid_int = int(qid)
        qname = q_names.get(name, name.capitalize())
        color = q_colors.get(str(qid)) or q_colors.get(name)
        if color and not str(color).startswith("#"):
            color = f"#{color}"
        _QUALITIES[qid_int] = (qname, color)
    for oid, name in res.get("originNames", {}).items():
        _ORIGINS[int(oid)] = name
    for eid, info in (res.get("attribute_controlled_attached_particles") or {}).items():
        if isinstance(info, dict):
            _EFFECTS[int(eid)] = info.get("name") or info.get("system")


def _load_items_game() -> None:
    path = CACHE_DIR / "items_game.txt"
    if not path.exists():
        logger.warning("Missing %s", path)
        return
    try:
        text = path.read_text()
        data = vdf.loads(text).get("items_game", {})
    except Exception as exc:  # pragma: no cover - corrupted file
        logger.warning("Failed reading %s: %s", path, exc)
        return
    for pid, info in data.get("paint_kits", {}).items():
        if not isinstance(info, dict):
            continue
        color = info.get("hex_color") or info.get("color")
        if color and not str(color).startswith("#"):
            color = f"#{color}"
        _PAINTS[int(pid)] = {"name": info.get("name"), "hex": color}
    for sid, name in data.get("sheens", {}).items():
        _SHEENS[int(sid)] = name if isinstance(name, str) else name.get("name")
    for kid, name in data.get("killstreakers", {}).items():
        _KILLSTREAKERS[int(kid)] = name if isinstance(name, str) else name.get("name")
    for bit, name in data.get("spells", {}).items():
        _SPELLS[int(bit)] = name if isinstance(name, str) else name.get("name")
    for aid, name in data.get("strange_parts", {}).items():
        _STRANGE_PARTS[int(aid)] = name if isinstance(name, str) else name.get("name")


_load_schema_items()
_load_schema_overview()
_load_items_game()


def get_item(defindex: int) -> Dict[str, Any]:
    if defindex not in _ITEMS:
        raise KeyError(defindex)
    return _ITEMS[defindex]


def get_quality(qid: int) -> Tuple[str, str | None] | None:
    if qid in _QUALITIES:
        return _QUALITIES[qid]
    logger.warning("Unknown quality id %s", qid)
    return None


def get_origin(oid: int) -> str | None:
    if oid in _ORIGINS:
        return _ORIGINS[oid]
    logger.warning("Unknown origin id %s", oid)
    return None


def get_paint(pid: int) -> Dict[str, str | None] | None:
    if pid in _PAINTS:
        return _PAINTS[pid]
    logger.warning("Unknown paint id %s", pid)
    return None


def get_effect(eid: int) -> str | None:
    if eid in _EFFECTS:
        return _EFFECTS[eid]
    logger.warning("Unknown effect id %s", eid)
    return None


def get_sheen(sid: int) -> str | None:
    if sid in _SHEENS:
        return _SHEENS[sid]
    logger.warning("Unknown sheen id %s", sid)
    return None


def get_killstreaker(kid: int) -> str | None:
    if kid in _KILLSTREAKERS:
        return _KILLSTREAKERS[kid]
    logger.warning("Unknown killstreaker id %s", kid)
    return None


def get_strange_part(attr_defindex: int) -> str | None:
    if attr_defindex in _STRANGE_PARTS:
        return _STRANGE_PARTS[attr_defindex]
    logger.warning("Unknown strange part %s", attr_defindex)
    return None


def get_spell(bit: int) -> str | None:
    if bit in _SPELLS:
        return _SPELLS[bit]
    logger.warning("Unknown spell bit %s", bit)
    return None


__all__ = [
    "get_item",
    "get_quality",
    "get_origin",
    "get_paint",
    "get_effect",
    "get_sheen",
    "get_killstreaker",
    "get_strange_part",
    "get_spell",
]
