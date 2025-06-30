"""Static TF2 lookup tables and helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

import vdf

BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = BASE_DIR / "cache" / "tf2_schema.json"
ITEMS_GAME_PATH = BASE_DIR / "cache" / "items_game_cleaned.json"
SCHEMA_FILE = SCHEMA_PATH
ITEMS_GAME_FILE = ITEMS_GAME_PATH

with SCHEMA_PATH.open() as f:
    _SCHEMA = json.load(f)
with ITEMS_GAME_PATH.open() as f:
    _ITEMS_GAME = json.load(f)

TF2_SCHEMA: Dict[str, Any] = _SCHEMA.get("items") or _SCHEMA
ITEMS_GAME_CLEANED: Dict[str, Any] = _ITEMS_GAME
EFFECT_NAMES: Dict[str, str] = _SCHEMA.get("effects", {})

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

for qid, name in [
    (0, "Normal"),
    (1, "Genuine"),
    (3, "Vintage"),
    (5, "Unusual"),
    (6, "Unique"),
    (11, "Strange"),
    (13, "Haunted"),
]:
    QUALITY_MAP.setdefault(
        qid, {"name": name, "hex": _COLOR_TABLE.get(name, "#B2B2B2")}
    )

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
_DEFAULT_SPELLS = {
    1: "Fire Footprints",
    2: "Voices From Below",
    4: "Pumpkin Bombs",
    8: "Exorcism",
    16: "Paint Spell",
}
for bit, name in _DEFAULT_SPELLS.items():
    SPELL_FLAGS.setdefault(bit, name)

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


def clean_items_game(raw: dict | str) -> Dict[str, Any]:
    """Return a simplified map of defindex -> item info."""

    if isinstance(raw, str):
        parsed = vdf.loads(raw)
    else:
        parsed = raw

    data = parsed.get("items_game", parsed)
    items = data.get("items", {})

    cleaned: Dict[str, Any] = {}
    for key, info in items.items():
        if not str(key).isdigit() or not isinstance(info, dict):
            continue
        cleaned[str(key)] = info
    return cleaned


def load_files(*, auto_refetch: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load local schema files and populate globals."""

    global TF2_SCHEMA, ITEMS_GAME_CLEANED, EFFECT_NAMES

    schema_path = Path(SCHEMA_FILE).resolve()
    if not schema_path.exists():
        raise RuntimeError(f"Missing {schema_path}")
    with schema_path.open() as f:
        data = json.load(f)

    items = data.get("items") or data
    if not isinstance(items, dict) or not items:
        raise RuntimeError("tf2_schema.json is empty or invalid")

    TF2_SCHEMA = items
    EFFECT_NAMES = data.get("effects", {}) if isinstance(data, dict) else {}
    print(f"\N{CHECK MARK} Loaded {len(TF2_SCHEMA)} items from {schema_path}")
    if len(TF2_SCHEMA) < 5000:
        print(
            "\N{WARNING SIGN} tf2_schema.json may be stale or incomplete. "
            "Consider forcing a refetch."
        )

    items_game_path = Path(ITEMS_GAME_FILE).resolve()
    if not items_game_path.exists():
        raise RuntimeError(f"Missing {items_game_path}")
    with items_game_path.open() as f:
        ITEMS_GAME_CLEANED = json.load(f)
    if not isinstance(ITEMS_GAME_CLEANED, dict) or not ITEMS_GAME_CLEANED:
        raise RuntimeError("items_game_cleaned.json is empty or invalid")
    print(
        f"\N{CHECK MARK} Cleaned items_game has {len(ITEMS_GAME_CLEANED)} entries from {items_game_path}"
    )
    if len(ITEMS_GAME_CLEANED) < 10000:
        print(
            "\N{WARNING SIGN} items_game_cleaned.json may be stale or incomplete. Consider a refresh."
        )
    return TF2_SCHEMA, ITEMS_GAME_CLEANED


__all__ = [
    "QUALITY_MAP",
    "ORIGIN_MAP",
    "PAINTS",
    "SHEENS",
    "KILLSTREAKERS",
    "SPELL_FLAGS",
    "STRANGE_PARTS",
    "EFFECTS",
    "TF2_SCHEMA",
    "ITEMS_GAME_CLEANED",
    "EFFECT_NAMES",
    "clean_items_game",
    "load_files",
]
