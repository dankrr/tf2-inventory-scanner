"""Static TF2 lookup tables built from cached JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = BASE_DIR / "cache" / "tf2_schema.json"
ITEMS_GAME_PATH = BASE_DIR / "cache" / "items_game_cleaned.json"

with SCHEMA_PATH.open() as f:
    _SCHEMA = json.load(f)
with ITEMS_GAME_PATH.open() as f:
    _ITEMS_GAME = json.load(f)

_COLOR_TABLE = {
    "Normal": "#B2B2B2",
    "Genuine": "#4D7455",
    "Vintage": "#476291",
    "Unusual": "#8650AC",
    "Unique": "#FFD700",
    "Strange": "#CF6A32",
    "Haunted": "#38F3AB",
}

QUALITY_MAP: Dict[int, Dict[str, str]] = {}
for k, v in (_SCHEMA.get("qualities") or {}).items():
    if str(k).isdigit():
        qid, name = int(k), str(v)
    else:
        qid, name = int(v), str(k)
    QUALITY_MAP[qid] = {"name": name, "hex": _COLOR_TABLE.get(name, "#B2B2B2")}

ORIGIN_MAP: Dict[int, str] = {
    int(k): str(v) for k, v in (_SCHEMA.get("originNames") or {}).items()
}

PAINTS: Dict[int, Dict[str, str]] = {
    int(pid): {"name": info.get("name", ""), "hex": info.get("hex", "")}
    for pid, info in (_ITEMS_GAME.get("paints") or {}).items()
}


def _enum(attr_id: int) -> Dict[int, str]:
    attr = (_ITEMS_GAME.get("attributes") or {}).get(str(attr_id), {})
    enum = attr.get("values") or attr.get("enum") or attr.get("enum_list") or {}
    return {int(k): str(v) for k, v in enum.items()}


SHEENS: Dict[int, str] = _enum(2014)
KILLSTREAKERS: Dict[int, str] = _enum(2071)

SPELL_FLAGS: Dict[int, str] = {
    int(bit): name for bit, name in (_ITEMS_GAME.get("spells") or {}).items()
}

STRANGE_PARTS: Dict[int, str] = {
    attr_id: name
    for attr_id, name in (
        {
            int(k): str(v.get("name", ""))
            for k, v in (_ITEMS_GAME.get("attributes") or {}).items()
        }
    ).items()
    if 380 <= attr_id <= 385
}

EFFECTS: Dict[int, str] = {
    int(k): str(v) for k, v in (_SCHEMA.get("effects") or {}).items()
}

__all__ = [
    "QUALITY_MAP",
    "ORIGIN_MAP",
    "PAINTS",
    "SHEENS",
    "KILLSTREAKERS",
    "SPELL_FLAGS",
    "STRANGE_PARTS",
    "EFFECTS",
]
