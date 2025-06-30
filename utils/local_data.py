import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple

import vdf

TF2_SCHEMA: Dict[str, Any] = {}
ITEMS_GAME_CLEANED: Dict[str, Any] = {}
EFFECT_NAMES: Dict[str, str] = {}

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_DIR = Path(os.getenv("TF2_SCHEMA_DIR", BASE_DIR / "cache"))
DEFINDEXES_FILE = SCHEMA_DIR / "defindexes.json"
EFFECTS_FILE = SCHEMA_DIR / "effects.json"
DEFAULT_ITEMS_GAME_FILE = BASE_DIR / "cache" / "items_game_cleaned.json"
ITEMS_GAME_FILE = Path(os.getenv("TF2_ITEMS_GAME_FILE", DEFAULT_ITEMS_GAME_FILE))


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

    schema_path = DEFINDEXES_FILE.resolve()
    if not schema_path.exists():
        raise RuntimeError(f"Missing {schema_path}")
    with schema_path.open() as f:
        TF2_SCHEMA = json.load(f)

    if not isinstance(TF2_SCHEMA, dict) or not TF2_SCHEMA:
        raise RuntimeError("defindexes.json is empty or invalid")

    effects_path = EFFECTS_FILE.resolve()
    EFFECT_NAMES = {}
    if effects_path.exists():
        with effects_path.open() as f:
            try:
                EFFECT_NAMES = json.load(f)
            except Exception:  # pragma: no cover - malformed file
                EFFECT_NAMES = {}

    print(f"\N{CHECK MARK} Loaded {len(TF2_SCHEMA)} items from {schema_path}")
    if len(TF2_SCHEMA) < 5000:
        print(
            "\N{WARNING SIGN} defindexes.json may be stale or incomplete. "
            "Consider a refresh."
        )

    items_game_path = ITEMS_GAME_FILE.resolve()
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
