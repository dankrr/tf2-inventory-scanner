import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple

import vdf

TF2_SCHEMA: Dict[str, Any] = {}
ITEMS_GAME_CLEANED: Dict[str, Any] = {}
EFFECT_NAMES: Dict[str, str] = {}
PAINT_NAMES: Dict[str, str] = {}
WEAR_NAMES: Dict[str, str] = {}
KILLSTREAK_NAMES: Dict[str, str] = {}
STRANGE_PART_NAMES: Dict[str, str] = {}
PAINTKIT_NAMES: Dict[str, str] = {}
CRATE_SERIES_NAMES: Dict[str, str] = {}

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA_FILE = BASE_DIR / "cache" / "tf2_schema.json"
DEFAULT_ITEMS_GAME_FILE = BASE_DIR / "cache" / "items_game_cleaned.json"
SCHEMA_FILE = Path(os.getenv("TF2_SCHEMA_FILE", DEFAULT_SCHEMA_FILE))
ITEMS_GAME_FILE = Path(os.getenv("TF2_ITEMS_GAME_FILE", DEFAULT_ITEMS_GAME_FILE))
DEFAULT_EFFECT_FILE = BASE_DIR / "cache" / "effect_names.json"
DEFAULT_PAINT_FILE = BASE_DIR / "cache" / "paint_names.json"
DEFAULT_WEAR_FILE = BASE_DIR / "cache" / "wear_names.json"
DEFAULT_KILLSTREAK_FILE = BASE_DIR / "cache" / "killstreak_names.json"
DEFAULT_STRANGE_PART_FILE = BASE_DIR / "cache" / "strange_part_names.json"
DEFAULT_PAINTKIT_FILE = BASE_DIR / "cache" / "paintkit_names.json"
DEFAULT_CRATE_SERIES_FILE = BASE_DIR / "cache" / "crate_series_names.json"
EFFECT_FILE = Path(os.getenv("TF2_EFFECT_FILE", DEFAULT_EFFECT_FILE))
PAINT_FILE = Path(os.getenv("TF2_PAINT_FILE", DEFAULT_PAINT_FILE))
WEAR_FILE = Path(os.getenv("TF2_WEAR_FILE", DEFAULT_WEAR_FILE))
KILLSTREAK_FILE = Path(os.getenv("TF2_KILLSTREAK_FILE", DEFAULT_KILLSTREAK_FILE))
STRANGE_PART_FILE = Path(os.getenv("TF2_STRANGE_PART_FILE", DEFAULT_STRANGE_PART_FILE))
PAINTKIT_FILE = Path(os.getenv("TF2_PAINTKIT_FILE", DEFAULT_PAINTKIT_FILE))
CRATE_SERIES_FILE = Path(os.getenv("TF2_CRATE_SERIES_FILE", DEFAULT_CRATE_SERIES_FILE))


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


def _load_json_map(path: Path) -> Dict[str, str]:
    """Return a JSON dictionary from ``path`` or an empty dict."""

    if not path.exists():
        return {}
    try:
        with path.open() as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def load_files(*, auto_refetch: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load local schema files and populate globals."""

    global TF2_SCHEMA, ITEMS_GAME_CLEANED, EFFECT_NAMES, PAINT_NAMES, WEAR_NAMES, KILLSTREAK_NAMES, STRANGE_PART_NAMES, PAINTKIT_NAMES, CRATE_SERIES_NAMES

    schema_path = SCHEMA_FILE.resolve()
    if not schema_path.exists():
        raise RuntimeError(f"Missing {schema_path}")
    with schema_path.open() as f:
        data = json.load(f)

    items = data.get("items") or data
    if not isinstance(items, dict) or not items:
        raise RuntimeError("tf2_schema.json is empty or invalid")

    if len(items) < 5000 and auto_refetch:
        try:
            from . import schema_fetcher

            api_key = os.getenv("STEAM_API_KEY")
            if not api_key:
                raise RuntimeError("STEAM_API_KEY is required for refetch")
            fetched = schema_fetcher._fetch_schema(api_key)
            schema_path.write_text(json.dumps(fetched))
            data = fetched
            items = fetched.get("items") or fetched
            print(f"Refetched TF2 schema: {len(items)} items -> {schema_path}")
        except Exception as exc:  # pragma: no cover - network failure
            print(f"Failed to refetch schema: {exc}")

    TF2_SCHEMA = items
    EFFECT_NAMES = data.get("effects", {}) if isinstance(data, dict) else {}
    print(f"\N{CHECK MARK} Loaded {len(TF2_SCHEMA)} items from {schema_path}")
    if len(TF2_SCHEMA) < 5000:
        print(
            "\N{WARNING SIGN} tf2_schema.json may be stale or incomplete. "
            "Consider forcing a refetch."
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

    EFFECT_NAMES = _load_json_map(EFFECT_FILE)
    PAINT_NAMES = _load_json_map(PAINT_FILE)
    WEAR_NAMES = _load_json_map(WEAR_FILE)
    KILLSTREAK_NAMES = _load_json_map(KILLSTREAK_FILE)
    STRANGE_PART_NAMES = _load_json_map(STRANGE_PART_FILE)
    PAINTKIT_NAMES = _load_json_map(PAINTKIT_FILE)
    CRATE_SERIES_NAMES = _load_json_map(CRATE_SERIES_FILE)

    for label, mapping, path in [
        ("effects", EFFECT_NAMES, EFFECT_FILE),
        ("paints", PAINT_NAMES, PAINT_FILE),
        ("wears", WEAR_NAMES, WEAR_FILE),
        ("killstreaks", KILLSTREAK_NAMES, KILLSTREAK_FILE),
        ("strange parts", STRANGE_PART_NAMES, STRANGE_PART_FILE),
        ("paintkits", PAINTKIT_NAMES, PAINTKIT_FILE),
        ("crate series", CRATE_SERIES_NAMES, CRATE_SERIES_FILE),
    ]:
        if mapping:
            print(f"\N{CHECK MARK} Loaded {len(mapping)} {label} from {path}")
    return TF2_SCHEMA, ITEMS_GAME_CLEANED
