import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple
import logging
import asyncio
import time

import vdf
from .schema_provider import SchemaProvider
from .steam_schema import SteamSchemaProvider
from .price_loader import ensure_currencies_cached
from . import constants as consts

# Legacy globals kept for backward compatibility
TF2_SCHEMA: Dict[str, Any] = {}
ITEMS_GAME_CLEANED: Dict[str, Any] = {}

# Cached schema maps
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
PAINTKIT_NAMES_BY_ID: Dict[str, str]
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
# Local schema cache files
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

# Path to combined Steam schema
DEFAULT_STEAM_SCHEMA_FILE = BASE_DIR / "data" / "schema_steam.json"
STEAM_SCHEMA_FILE = Path(os.getenv("TF2_STEAM_SCHEMA_FILE", DEFAULT_STEAM_SCHEMA_FILE))

# Path to static exclusions file
DEFAULT_EXCLUSIONS_FILE = BASE_DIR / "static" / "exclusions.json"
EXCLUSIONS_FILE = Path(os.getenv("TF2_EXCLUSIONS_FILE", DEFAULT_EXCLUSIONS_FILE))


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


def load_exclusions() -> Dict[str, Any]:
    """Return exclusions configuration from :data:`EXCLUSIONS_FILE`."""

    if not EXCLUSIONS_FILE.exists():
        return {}
    try:
        with EXCLUSIONS_FILE.open() as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _normalize_image_url(url: str | None) -> str | None:
    """Return ``url`` with an HTTPS scheme for Steam CDN links."""

    if isinstance(url, str) and url.startswith("http://media.steampowered.com"):
        return url.replace(
            "http://media.steampowered.com",
            "https://media.steampowered.com",
            1,
        )
    return url


# Preload cached paintkit names at import time
warpaints = load_json("schema/warpaints.json")
PAINTKIT_NAMES = (
    {str(k): v for k, v in warpaints.items()} if isinstance(warpaints, dict) else {}
)
PAINTKIT_NAMES_BY_ID = {str(v): k for k, v in PAINTKIT_NAMES.items()}


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
    """Load local schema files from the local cache."""

    global SCHEMA_ATTRIBUTES, ITEMS_BY_DEFINDEX, QUALITIES_BY_INDEX, PARTICLE_NAMES
    global EFFECT_NAMES, PAINT_NAMES, WEAR_NAMES, KILLSTREAK_NAMES, STRANGE_PART_NAMES, PAINTKIT_NAMES, CRATE_SERIES_NAMES
    global FOOTPRINT_SPELL_MAP, PAINT_SPELL_MAP

    schema_path = STEAM_SCHEMA_FILE.resolve()
    curr_path = CURRENCIES_FILE.resolve()
    optional = {"string_lookups": STRING_LOOKUPS_FILE.resolve()}

    need_schema = not schema_path.exists()
    if schema_path.exists() and auto_refetch:
        age = time.time() - schema_path.stat().st_mtime
        if age >= SteamSchemaProvider.TTL:
            need_schema = True

    if need_schema:
        if not auto_refetch:
            raise RuntimeError(f"Missing {schema_path}")
        provider = SteamSchemaProvider(cache_file=schema_path)
        schema = asyncio.run(provider.load_schema(force=True))
        if verbose:
            logging.info(
                "\N{DOWNWARDS ARROW WITH TIP LEFTWARDS} Downloaded %s", schema_path
            )
    else:
        with schema_path.open() as f:
            schema = json.load(f)

    optional_missing = {k: p for k, p in optional.items() if not p.exists()}
    if optional_missing and auto_refetch:
        for key, path in optional_missing.items():
            provider = SchemaProvider(cache_dir=path.parent)
            provider._load(key, provider.ENDPOINTS[key], force=True)
            if verbose:
                logging.info(
                    "\N{DOWNWARDS ARROW WITH TIP LEFTWARDS} Downloaded %s", path
                )

    attr_path = schema_path
    raw_attrs = schema.get("attributes_by_defindex", {})
    if isinstance(raw_attrs, dict):
        SCHEMA_ATTRIBUTES = {
            int(k): v for k, v in raw_attrs.items() if str(k).isdigit()
        }
    else:
        SCHEMA_ATTRIBUTES = {}
    if verbose:
        logging.info(
            "\N{CHECK MARK} Loaded %d attributes from %s",
            len(SCHEMA_ATTRIBUTES),
            attr_path,
        )

    raw_items = schema.get("items_by_defindex", {})
    items_map: Dict[int, Any] = {}
    if isinstance(raw_items, dict):
        for k, v in raw_items.items():
            if not str(k).isdigit() or not isinstance(v, dict):
                continue
            idx = int(k)
            v["image_url"] = _normalize_image_url(v.get("image_url"))
            v["image_url_large"] = _normalize_image_url(v.get("image_url_large"))
            items_map[idx] = v
    ITEMS_BY_DEFINDEX = items_map
    if verbose:
        logging.info(
            "\N{CHECK MARK} Loaded %d items from %s",
            len(ITEMS_BY_DEFINDEX),
            schema_path,
        )
        if len(ITEMS_BY_DEFINDEX) < 5000:
            logging.info(
                "\N{WARNING SIGN} items.json may be stale or incomplete. Consider a refresh."
            )

    raw_quals = schema.get("qualities_by_index", {})
    if isinstance(raw_quals, dict):
        by_key = {int(k): str(v) for k, v in raw_quals.items() if str(k).isdigit()}
        by_val = {int(v): str(k) for k, v in raw_quals.items() if str(v).isdigit()}
        QUALITIES_BY_INDEX = by_key or by_val
    else:
        QUALITIES_BY_INDEX = {}

    if QUALITIES_BY_INDEX:
        rarity_map = {
            "rarity1": "Normal",
            "rarity2": "Genuine",
            "rarity3": "Vintage",
            "rarity4": "Unusual",
        }
        for idx, name in list(QUALITIES_BY_INDEX.items()):
            canon = rarity_map.get(name)
            if canon:
                QUALITIES_BY_INDEX[idx] = canon
    if verbose:
        logging.info(
            "\N{CHECK MARK} Loaded %d qualities from %s",
            len(QUALITIES_BY_INDEX),
            schema_path,
        )

    raw_parts = schema.get("particles_by_index", {})
    if isinstance(raw_parts, dict):
        PARTICLE_NAMES = {
            int(k): str(v) for k, v in raw_parts.items() if str(k).isdigit()
        }
    else:
        PARTICLE_NAMES = {}
    if verbose:
        logging.info(
            "\N{CHECK MARK} Loaded %d particles from %s",
            len(PARTICLE_NAMES),
            schema_path,
        )

    origins = schema.get("origins_by_index", {})
    consts.ORIGIN_MAP.clear()
    if isinstance(origins, dict):
        consts.ORIGIN_MAP.update({int(k): str(v) for k, v in origins.items()})

    if not curr_path.exists():
        if not auto_refetch:
            raise RuntimeError(f"Missing {curr_path}")
        ensure_currencies_cached(refresh=True)
        if verbose:
            logging.info(
                "\N{DOWNWARDS ARROW WITH TIP LEFTWARDS} Downloaded %s", curr_path
            )
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
