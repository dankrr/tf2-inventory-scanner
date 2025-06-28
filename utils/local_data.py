import json
from pathlib import Path
from typing import Any, Dict, Tuple

import vdf

TF2_SCHEMA: Dict[str, Any] = {}
ITEMS_GAME_CLEANED: Dict[str, Any] = {}
EFFECT_NAMES: Dict[str, str] = {}

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_FILE = BASE_DIR / "data" / "tf2_schema.json"
ITEMS_GAME_FILE = BASE_DIR / "data" / "items_game_cleaned.json"


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


def load_files() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load local schema files and populate globals."""
    global TF2_SCHEMA, ITEMS_GAME_CLEANED, EFFECT_NAMES

    if not SCHEMA_FILE.exists():
        raise RuntimeError(f"Missing {SCHEMA_FILE}")
    with SCHEMA_FILE.open() as f:
        data = json.load(f)
    items = data.get("items") or data
    if not isinstance(items, dict) or not items:
        raise RuntimeError("tf2_schema.json is empty or invalid")
    TF2_SCHEMA = items
    EFFECT_NAMES = data.get("effects", {}) if isinstance(data, dict) else {}
    print(f"\N{CHECK MARK} Loaded {len(TF2_SCHEMA)} items from {SCHEMA_FILE}")
    if len(TF2_SCHEMA) < 100:
        print(
            "\N{WARNING SIGN} tf2_schema.json may be stale or incomplete. "
            "Consider forcing a refetch."
        )

    if not ITEMS_GAME_FILE.exists():
        raise RuntimeError(f"Missing {ITEMS_GAME_FILE}")
    with ITEMS_GAME_FILE.open() as f:
        ITEMS_GAME_CLEANED = json.load(f)
    if not isinstance(ITEMS_GAME_CLEANED, dict) or not ITEMS_GAME_CLEANED:
        raise RuntimeError("items_game_cleaned.json is empty or invalid")
    print(f"\N{CHECK MARK} Cleaned items_game has {len(ITEMS_GAME_CLEANED)} entries")
    return TF2_SCHEMA, ITEMS_GAME_CLEANED
