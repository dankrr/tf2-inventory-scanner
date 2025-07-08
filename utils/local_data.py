import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple
import logging

import vdf
from .schema_provider import SchemaProvider
from .price_loader import ensure_currencies_cached

# Legacy globals kept for backward compatibility
TF2_SCHEMA: Dict[str, Any] = {}
ITEMS_GAME_CLEANED: Dict[str, Any] = {}

# New schema maps sourced from schema.autobot.tf
SCHEMA_ATTRIBUTES: Dict[int, Dict[str, Any]] = {}
ITEMS_BY_DEFINDEX: Dict[int, Dict[str, Any]] = {}
QUALITIES_BY_INDEX: Dict[int, str] = {}
PARTICLE_NAMES: Dict[int, str] = {}
EFFECT_NAMES: Dict[str, str] = {}
PAINT_NAMES: Dict[str, str] = {}
WEAR_NAMES: Dict[str, str] = {}
KILLSTREAK_NAMES: Dict[str, str] = {}
STRANGE_PART_NAMES: Dict[str, str] = {}
# will be populated at import time
PAINTKIT_NAMES: Dict[str, str]
CRATE_SERIES_NAMES: Dict[str, str] = {}
CURRENCIES: Dict[str, Any] = {}
FOOTPRINT_SPELL_MAP: Dict[int, str] = {}
PAINT_SPELL_MAP: Dict[int, str] = {}
KILLSTREAK_EFFECT_NAMES: Dict[str, str] = {
    "2002": "Fire Horns",
    "2003": "Cerebral Discharge",
    "2004": "Tornado",
    "2005": "Flames",
    "2006": "Singularity",
    "2007": "Incinerator",
    "2008": "Hypno-Beam",

}

# Map of attribute class -> in-game spell name
SPELL_DISPLAY_NAMES: Dict[str, str] = {
    "halloween_voice_modulation": "Voices From Below",
    "halloween_pumpkin_explosions": "Pumpkin Bombs",
    "halloween_green_flames": "Halloween Fire",
    "halloween_death_ghosts": "Exorcism",
    "halloween_footstep_type": "Halloween Footprints",
    "set_item_tint_rgb_override": "Die Job (Purple/Green Paint)",
    "set_item_tint_rgb_unusual": "Chromatic Corruption",
    "set_item_texture_wear_override": "Spectral Spectrum",
    "set_item_color_wear_override": "Sinister Staining",
}

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent
# schema.autobot.tf cache files
DEFAULT_ATTRIBUTES_FILE = BASE_DIR / "cache" / "schema" / "attributes.json"
DEFAULT_PARTICLES_FILE = BASE_DIR / "cache" / "schema" / "particles.json"
DEFAULT_ITEMS_FILE = BASE_DIR / "cache" / "schema" / "items.json"
DEFAULT_QUALITIES_FILE = BASE_DIR / "cache" / "schema" / "qualities.json"
DEFAULT_CURRENCIES_FILE = BASE_DIR / "cache" / "currencies.json"

ATTRIBUTES_FILE = Path(os.getenv("TF2_ATTRIBUTES_FILE", DEFAULT_ATTRIBUTES_FILE))
PARTICLES_FILE = Path(os.getenv("TF2_PARTICLES_FILE", DEFAULT_PARTICLES_FILE))
ITEMS_FILE = Path(os.getenv("TF2_ITEMS_FILE", DEFAULT_ITEMS_FILE))
QUALITIES_FILE = Path(os.getenv("TF2_QUALITIES_FILE", DEFAULT_QUALITIES_FILE))
CURRENCIES_FILE = Path(os.getenv("TF2_CURRENCIES_FILE", DEFAULT_CURRENCIES_FILE))
DEFAULT_EFFECT_FILE = BASE_DIR / "cache" / "schema" / "effects.json"
DEFAULT_PAINT_FILE = BASE_DIR / "cache" / "schema" / "paints.json"
DEFAULT_WEAR_FILE = BASE_DIR / "cache" / "wear_names.json"
DEFAULT_KILLSTREAK_FILE = BASE_DIR / "cache" / "killstreak_names.json"
DEFAULT_KS_EFFECT_FILE = BASE_DIR / "cache" / "killstreak_effect_names.json"
DEFAULT_STRANGE_PART_FILE = BASE_DIR / "cache" / "strange_part_names.json"
# Cached warpaint names from the paintkits endpoint
DEFAULT_PAINTKIT_FILE = BASE_DIR / "cache" / "schema" / "warpaints.json"
DEFAULT_CRATE_SERIES_FILE = BASE_DIR / "cache" / "crate_series_names.json"
DEFAULT_STRING_LOOKUPS_FILE = BASE_DIR / "cache" / "string_lookups.json"
EFFECT_FILE = Path(os.getenv("TF2_EFFECT_FILE", DEFAULT_EFFECT_FILE))
DEFAULT_EFFECT_NAMES_FILE = BASE_DIR / "data" / "effect_names.json"
EFFECT_NAMES_FILE = Path(os.getenv("TF2_EFFECT_NAMES_FILE", DEFAULT_EFFECT_NAMES_FILE))
PAINT_FILE = Path(os.getenv("TF2_PAINT_FILE", DEFAULT_PAINT_FILE))
WEAR_FILE = Path(os.getenv("TF2_WEAR_FILE", DEFAULT_WEAR_FILE))
KILLSTREAK_FILE = Path(os.getenv("TF2_KILLSTREAK_FILE", DEFAULT_KILLSTREAK_FILE))
KILLSTREAK_EFFECT_FILE = Path(os.getenv("TF2_KS_EFFECT_FILE", DEFAULT_KS_EFFECT_FILE))
STRANGE_PART_FILE = Path(os.getenv("TF2_STRANGE_PART_FILE", DEFAULT_STRANGE_PART_FILE))
PAINTKIT_FILE = Path(os.getenv("TF2_PAINTKIT_FILE", DEFAULT_PAINTKIT_FILE))
CRATE_SERIES_FILE = Path(os.getenv("TF2_CRATE_SERIES_FILE", DEFAULT_CRATE_SERIES_FILE))
STRING_LOOKUPS_FILE = Path(
    os.getenv("TF2_STRING_LOOKUPS_FILE", DEFAULT_STRING_LOOKUPS_FILE)
)


def load_json(relative: str) -> Any:
    """Return parsed JSON from ``BASE_DIR / "cache" / relative`` or ``{}``."""

    path = BASE_DIR / "cache" / relative
    if not path.exists():
        return {}
    try:
        with path.open() as f:
            return json.load(f)
    except Exception:
        return {}


# Preload cached paintkit names at import time
warpaints = load_json("schema/warpaints.json")
PAINTKIT_NAMES = (
    {str(k): v for k, v in warpaints.items()} if isinstance(warpaints, dict) else {}
)


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


def _load_paint_id_map(path: Path) -> Dict[str, str]:
    """Return a mapping of paint ID -> name from a name->id JSON file."""

    if not path.exists():
        return {}
    try:
        with path.open() as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {str(v): str(k) for k, v in data.items() if str(v).isdigit()}
    except Exception:
        pass
    return {}


def load_files(
    *, auto_refetch: bool = False, verbose: bool = False
) -> Tuple[Dict[int, Any], Dict[int, Any]]:
    """Load local schema files from the schema.autobot.tf cache."""

    global SCHEMA_ATTRIBUTES, ITEMS_BY_DEFINDEX, QUALITIES_BY_INDEX, PARTICLE_NAMES
    global EFFECT_NAMES, PAINT_NAMES, WEAR_NAMES, KILLSTREAK_NAMES, STRANGE_PART_NAMES, PAINTKIT_NAMES, CRATE_SERIES_NAMES
    global FOOTPRINT_SPELL_MAP, PAINT_SPELL_MAP

    required = {
        "attributes": ATTRIBUTES_FILE.resolve(),
        "items": ITEMS_FILE.resolve(),
        "qualities": QUALITIES_FILE.resolve(),
        "particles": PARTICLES_FILE.resolve(),
        "currencies": CURRENCIES_FILE.resolve(),
    }
    optional = {"string_lookups": STRING_LOOKUPS_FILE.resolve()}

    missing = {k: p for k, p in required.items() if not p.exists()}
    if missing:
        if not auto_refetch:
            raise RuntimeError("Missing " + ", ".join(str(p) for p in missing.values()))
        provider = SchemaProvider(cache_dir=required["attributes"].parent)
        for key, path in missing.items():
            if key == "currencies":
                ensure_currencies_cached(refresh=True)
            else:
                provider._load(key, provider.ENDPOINTS[key], force=True)
            if verbose:
                logging.info(
                    "\N{DOWNWARDS ARROW WITH TIP LEFTWARDS} Downloaded %s", path
                )

    optional_missing = {k: p for k, p in optional.items() if not p.exists()}
    if optional_missing and auto_refetch:
        for key, path in optional_missing.items():
            provider = SchemaProvider(cache_dir=path.parent)
            provider._load(key, provider.ENDPOINTS[key], force=True)
            if verbose:
                logging.info(
                    "\N{DOWNWARDS ARROW WITH TIP LEFTWARDS} Downloaded %s", path
                )

    attr_path = required["attributes"]
    with attr_path.open() as f:
        data = json.load(f)
    raw_attrs = data["value"] if isinstance(data, dict) and "value" in data else data
    mapping: Dict[int, Any] = {}
    if isinstance(raw_attrs, list):
        for entry in raw_attrs:
            if not isinstance(entry, dict) or "defindex" not in entry:
                continue
            try:
                idx = int(entry["defindex"])
            except (TypeError, ValueError):
                continue
            mapping[idx] = entry
    elif isinstance(raw_attrs, dict):
        mapping = {int(k): v for k, v in raw_attrs.items() if str(k).isdigit()}
    SCHEMA_ATTRIBUTES = mapping
    if verbose:
        logging.info(
            "\N{CHECK MARK} Loaded %d attributes from %s",
            len(SCHEMA_ATTRIBUTES),
            attr_path,
        )

    items_path = required["items"]
    if not items_path.exists():
        raise RuntimeError(f"Missing {items_path}")
    with items_path.open() as f:
        data = json.load(f)
    raw_items = data["value"] if isinstance(data, dict) and "value" in data else data
    items_map: Dict[int, Any] = {}
    if isinstance(raw_items, list):
        for entry in raw_items:
            if not isinstance(entry, dict) or "defindex" not in entry:
                continue
            try:
                idx = int(entry["defindex"])
            except (TypeError, ValueError):
                continue
            items_map[idx] = entry
    elif isinstance(raw_items, dict):
        items_map = {int(k): v for k, v in raw_items.items() if str(k).isdigit()}
    ITEMS_BY_DEFINDEX = items_map
    if verbose:
        logging.info(
            "\N{CHECK MARK} Loaded %d items from %s", len(ITEMS_BY_DEFINDEX), items_path
        )
        if len(ITEMS_BY_DEFINDEX) < 5000:
            logging.info(
                "\N{WARNING SIGN} items.json may be stale or incomplete. Consider a refresh."
            )

    qual_path = required["qualities"]
    if not qual_path.exists():
        raise RuntimeError(f"Missing {qual_path}")
    with qual_path.open() as f:
        data = json.load(f)
    raw_quals = data["value"] if isinstance(data, dict) and "value" in data else data
    if isinstance(raw_quals, list):
        QUALITIES_BY_INDEX = {
            int(e["id"]): str(e["name"])
            for e in raw_quals
            if isinstance(e, dict) and "id" in e and "name" in e
        }
    elif isinstance(raw_quals, dict):
        by_key = {int(k): str(v) for k, v in raw_quals.items() if str(k).isdigit()}
        by_value = {int(v): str(k) for k, v in raw_quals.items() if str(v).isdigit()}
        QUALITIES_BY_INDEX = by_key or by_value
    else:
        QUALITIES_BY_INDEX = {}
    if verbose:
        logging.info(
            "\N{CHECK MARK} Loaded %d qualities from %s",
            len(QUALITIES_BY_INDEX),
            qual_path,
        )

    particle_path = required["particles"]
    if not particle_path.exists():
        raise RuntimeError(f"Missing {particle_path}")
    with particle_path.open() as f:
        data = json.load(f)
    raw_parts = data["value"] if isinstance(data, dict) and "value" in data else data
    PARTICLE_NAMES = {
        int(e.get("id")): str(e.get("name"))
        for e in raw_parts
        if isinstance(e, dict) and "id" in e and "name" in e
    }
    if verbose:
        logging.info(
            "\N{CHECK MARK} Loaded %d particles from %s",
            len(PARTICLE_NAMES),
            particle_path,
        )

    curr_path = required["currencies"]
    if not curr_path.exists():
        raise RuntimeError(f"Missing {curr_path}")
    with curr_path.open() as f:
        data = json.load(f)
    raw_curr = (
        data.get("response", {}).get("currencies") if isinstance(data, dict) else data
    )
    if isinstance(raw_curr, dict):
        CURRENCIES.update(raw_curr)
    else:
        CURRENCIES.clear()
    if verbose:
        logging.info(
            "\N{CHECK MARK} Loaded %d currencies from %s",
            len(CURRENCIES),
            curr_path,
        )

    EFFECT_NAMES = _load_json_map(EFFECT_FILE)
    extra = _load_json_map(EFFECT_NAMES_FILE)
    if extra:
        EFFECT_NAMES.update(extra)
    PAINT_NAMES = _load_paint_id_map(PAINT_FILE)
    WEAR_NAMES = _load_json_map(WEAR_FILE)
    KILLSTREAK_NAMES = _load_json_map(KILLSTREAK_FILE)
    KILLSTREAK_EFFECT_NAMES = _load_json_map(KILLSTREAK_EFFECT_FILE)
    STRANGE_PART_NAMES = _load_json_map(STRANGE_PART_FILE)
    CRATE_SERIES_NAMES = _load_json_map(CRATE_SERIES_FILE)

    FOOTPRINT_SPELL_MAP = {}
    PAINT_SPELL_MAP = {}
    if STRING_LOOKUPS_FILE.exists():
        try:
            with STRING_LOOKUPS_FILE.open() as f:
                data = json.load(f)
            tables = (
                data["value"] if isinstance(data, dict) and "value" in data else data
            )
            if isinstance(tables, list):
                for table in tables:
                    if not isinstance(table, dict):
                        continue
                    name = str(table.get("table_name", "")).lower()
                    entries = table.get("strings", [])
                    if not isinstance(entries, list):
                        continue
                    mapping = {
                        int(e.get("index")): str(e.get("string"))
                        for e in entries
                        if isinstance(e, dict)
                        and "index" in e
                        and "string" in e
                        and str(e.get("index")).lstrip("-").isdigit()
                    }
                    if "footstep" in name or "footprint" in name:
                        FOOTPRINT_SPELL_MAP.update(mapping)
                    elif "tint" in name:
                        PAINT_SPELL_MAP.update(mapping)
        except Exception:
            FOOTPRINT_SPELL_MAP = {}
            PAINT_SPELL_MAP = {}
    else:
        FOOTPRINT_SPELL_MAP = {}
        PAINT_SPELL_MAP = {}

    if FOOTPRINT_SPELL_MAP or PAINT_SPELL_MAP:
        total = len(FOOTPRINT_SPELL_MAP) + len(PAINT_SPELL_MAP)
        if verbose:
            logging.info(
                "\N{CHECK MARK} Loaded %d spell lookups from %s",
                total,
                STRING_LOOKUPS_FILE,
            )

    for label, mapping, path in [
        ("effects", EFFECT_NAMES, EFFECT_NAMES_FILE),
        ("paints", PAINT_NAMES, PAINT_FILE),
        ("wears", WEAR_NAMES, WEAR_FILE),
        ("killstreaks", KILLSTREAK_NAMES, KILLSTREAK_FILE),
        ("killstreak effects", KILLSTREAK_EFFECT_NAMES, KILLSTREAK_EFFECT_FILE),
        ("strange parts", STRANGE_PART_NAMES, STRANGE_PART_FILE),
        ("paintkits", PAINTKIT_NAMES, PAINTKIT_FILE),
        ("crate series", CRATE_SERIES_NAMES, CRATE_SERIES_FILE),
    ]:
        if mapping and verbose:
            logging.info(
                "\N{CHECK MARK} Loaded %d %s from %s",
                len(mapping),
                label,
                path,
            )
    return SCHEMA_ATTRIBUTES, ITEMS_BY_DEFINDEX
