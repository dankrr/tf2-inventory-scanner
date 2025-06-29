import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple

import vdf

TF2_SCHEMA: Dict[str, Any] = {}
ITEMS_GAME_CLEANED: Dict[str, Any] = {}
EFFECT_NAMES: Dict[str, str] = {}

BASE_DIR = Path(__file__).resolve().parent.parent

# Default locations for Autobot schema files
SCHEMA_DIR = BASE_DIR / "cache" / "schema"
ITEMS_GAME_DIR = BASE_DIR / "cache" / "items_game"
PROPERTIES_DIR = BASE_DIR / "cache" / "properties"

DEFAULT_SCHEMA_ITEMS_FILE = SCHEMA_DIR / "items.json"
DEFAULT_ITEMS_GAME_FILE = ITEMS_GAME_DIR / "items.json"
DEFAULT_EFFECTS_FILE = PROPERTIES_DIR / "effects.json"

SCHEMA_ITEMS_FILE = Path(os.getenv("TF2_SCHEMA_ITEMS_FILE", DEFAULT_SCHEMA_ITEMS_FILE))
ITEMS_GAME_FILE = Path(os.getenv("TF2_ITEMS_GAME_FILE", DEFAULT_ITEMS_GAME_FILE))
EFFECTS_FILE = Path(os.getenv("TF2_EFFECTS_FILE", DEFAULT_EFFECTS_FILE))


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
    """Load Autobot schema files and populate globals."""

    global TF2_SCHEMA, ITEMS_GAME_CLEANED, EFFECT_NAMES

    schema_path = SCHEMA_ITEMS_FILE.resolve()
    if not schema_path.exists():
        raise RuntimeError(f"Missing {schema_path}")
    with schema_path.open() as f:
        items = json.load(f)

    if not isinstance(items, dict) or not items:
        raise RuntimeError("schema/items.json is empty or invalid")

    TF2_SCHEMA = items
    print(f"\N{CHECK MARK} Loaded {len(TF2_SCHEMA)} items from {schema_path}")
    if len(TF2_SCHEMA) < 5000:
        print(
            "\N{WARNING SIGN} schema/items.json may be stale or incomplete. "
            "Consider forcing a refetch."
        )

    effects_path = EFFECTS_FILE.resolve()
    if effects_path.exists():
        with effects_path.open() as f:
            EFFECT_NAMES = json.load(f)
    else:
        EFFECT_NAMES = {}

    items_game_path = ITEMS_GAME_FILE.resolve()
    if not items_game_path.exists():
        raise RuntimeError(f"Missing {items_game_path}")
    with items_game_path.open() as f:
        data = json.load(f)

    ITEMS_GAME_CLEANED = data.get("items", data)
    if not isinstance(ITEMS_GAME_CLEANED, dict) or not ITEMS_GAME_CLEANED:
        raise RuntimeError("items_game/items.json is empty or invalid")
    print(
        f"\N{CHECK MARK} Loaded items_game with {len(ITEMS_GAME_CLEANED)} entries from {items_game_path}"
    )
    if len(ITEMS_GAME_CLEANED) < 10000:
        print(
            "\N{WARNING SIGN} items_game/items.json may be stale or incomplete. Consider a refresh."
        )

    return TF2_SCHEMA, ITEMS_GAME_CLEANED
