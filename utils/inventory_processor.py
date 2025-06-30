from typing import Any, Dict, List, Tuple
import logging

import json
from pathlib import Path
from typing import Optional

from . import steam_api_client, schema_fetcher

logger = logging.getLogger(__name__)

# Base URL for item images
CLOUD = "https://steamcommunity-a.akamaihd.net/economy/image/"

# Mapping of defindex -> human readable name for warpaints
MAPPING_FILE = Path(__file__).with_name("warpaint_mapping.json")
WARPAINT_MAP: Dict[str, str] = {}
if MAPPING_FILE.exists():
    with MAPPING_FILE.open() as f:
        WARPAINT_MAP = json.load(f)

# Directory holding cached schema and property files
CACHE_DIR = Path("cache")

# property names available from schema.autobot.tf
PROPERTIES = [
    "qualities",
    "killstreaks",
    "effects",
    "paintkits",
    "wears",
    "paints",
    "strangeParts",
    "crateseries",
    "craftWeapons",
    "uncraftWeapons",
]

# Loaded property data
PROPS: Dict[str, Any] = {}
ITEMS_GAME: Dict[str, Any] = {}
SCHEMA_DATA: Dict[str, Any] = {}


def _load_schema() -> Dict[str, Any]:
    """Return cached AutoBot TF2 schema."""

    path = CACHE_DIR / "tf2_schema.json"
    if not path.exists():
        return {}
    try:
        with path.open() as fh:
            return json.load(fh)
    except Exception:  # pragma: no cover - corrupt file
        logger.warning("Failed to read %s", path)
        return {}


def _load_items_game() -> Dict[str, Any]:
    """Parse items_game.txt and return a mapping of defindex -> icon filename."""

    mapping: Dict[str, Any] = {}
    path = CACHE_DIR / "items_game.txt"
    if not path.exists():
        return mapping
    current: Optional[str] = None
    icon: Optional[str] = None
    name: Optional[str] = None
    try:
        with path.open() as fh:
            for line in fh:
                line = line.strip()
                if line.startswith('"'):
                    parts = line.split('"')
                    if len(parts) >= 3:
                        key = parts[1]
                        value = parts[3] if len(parts) > 3 else None
                        if key == "defindex":
                            current = value
                            icon = None
                            name = None
                        elif key == "image_inventory" and current:
                            icon = value
                        elif key == "name" and current and not name:
                            name = value
                if line == "}" and current:
                    mapping[current] = {"icon": icon, "name": name}
                    current = None
    except Exception:
        logger.warning("Failed parsing %s", path)
    return mapping


# Map of quality ID to (name, background color)
QUALITY_MAP = {
    0: ("Normal", "#B2B2B2"),
    1: ("Genuine", "#4D7455"),
    3: ("Vintage", "#476291"),
    5: ("Unusual", "#8650AC"),
    6: ("Unique", "#FFD700"),
    11: ("Strange", "#CF6A32"),
    13: ("Haunted", "#38F3AB"),
}


def _load_props() -> None:
    """Load property files from the cache directory."""

    global PROPS
    for name in PROPERTIES:
        path = CACHE_DIR / f"{name}.json"
        if not path.exists():
            continue
        try:
            with path.open() as fh:
                PROPS[name] = json.load(fh)
        except Exception:
            logger.warning("Failed to load %s", path)


def load_cached_data() -> None:
    """Populate global lookup tables from the cache directory."""

    global ITEMS_GAME, SCHEMA_DATA
    if not PROPS:
        _load_props()
    if not ITEMS_GAME:
        ITEMS_GAME = _load_items_game()
    if not SCHEMA_DATA:
        SCHEMA_DATA = _load_schema()


def fetch_inventory(steamid: str) -> Tuple[Dict[str, Any], str]:
    """Return inventory data and status using the Steam API helper."""

    status, data = steam_api_client.fetch_inventory(steamid)
    if status not in ("parsed", "incomplete"):
        data = {"items": []}
    else:
        data = data or {"items": []}
    return data, status


def enrich_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a list of inventory items enriched with schema info."""
    load_cached_data()

    items_raw = data.get("items")
    if not isinstance(items_raw, list):
        return []

    items: List[Dict[str, Any]] = []
    schema_map = schema_fetcher.SCHEMA or {}

    for asset in items_raw:
        defindex = str(asset.get("defindex", "0"))
        entry = schema_map.get(defindex)
        if not entry:
            continue

        icon_url = asset.get("icon_url") or asset.get("icon_url_large")
        if not icon_url:
            from_items = ITEMS_GAME.get(defindex, {})
            icon_url = from_items.get("icon")

        if icon_url:
            image_path = icon_url
            if icon_url.startswith("//"):
                final_url = "https:" + icon_url
            elif icon_url.startswith("http"):
                final_url = icon_url
            else:
                final_url = f"{CLOUD}{icon_url}/360fx360f"
        else:
            image_path = entry.get("image_url") or entry.get("image_url_large") or ""
            if image_path.startswith("http"):
                final_url = image_path
            else:
                final_url = f"{CLOUD}{image_path}" if image_path else ""

        name = (
            WARPAINT_MAP.get(defindex)
            or ITEMS_GAME.get(defindex, {}).get("name")
            or entry.get("item_name")
            or entry.get("name")
            or f"Item #{defindex}"
        )

        quality_id = asset.get("quality", 0)
        q_name, q_col = QUALITY_MAP.get(quality_id, ("Unknown", "#B2B2B2"))

        enriched = {
            "custom_name": asset.get("custom_name"),
            "custom_description": asset.get("custom_description"),
            "attributes": asset.get("attributes", []),
        }

        items.append(
            {
                "defindex": defindex,
                "name": name,
                "quality": q_name,
                "quality_color": q_col,
                "image_url": image_path,
                "final_url": final_url,
                "enriched": enriched,
            }
        )
    return items


def process_inventory(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Public wrapper that sorts items by name."""
    items = enrich_inventory(data)
    return sorted(items, key=lambda i: i["name"])
