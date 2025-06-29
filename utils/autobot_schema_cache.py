import json
import logging
from pathlib import Path
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://schema.autobot.tf"
CACHE_DIR = Path("cache")

PROPERTIES = {
    "defindexes": "defindexes.json",
    "qualities": "qualities.json",
    "killstreaks": "killstreaks.json",
    "effects": "effects.json",
    "paintkits": "paintkits.json",
    "wears": "wears.json",
    "crateseries": "crateseries.json",
    "paints": "paints.json",
    "strangeParts": "strange_parts.json",
    "craftWeapons": "craft_weapons.json",
    "uncraftWeapons": "uncraft_weapons.json",
}

# The "s" slug used to exist for Scout weapons but the endpoint now returns
# a 400 error. Skip it until the API exposes valid slugs again.
CLASS_CHARS = ["p", "m", "d", "e", "h", "t", "l", "g"]

GRADE_FILES = {
    "v1": "item_grade_v1.json",
    "v2": "item_grade_v2.json",
}

BASE_ENDPOINTS = {
    "tf2_schema.json": "/schema/download",
    "items_game.json": "/raw/items_game/current",
}


def _fetch_json(url: str) -> Dict[str, Any]:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def _ensure_file(path: Path, url: str, refresh: bool) -> None:
    if refresh or not path.exists():
        data = _fetch_json(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        logger.info("cached %s", path)


def ensure_all_cached(refresh: bool = False) -> None:
    """Ensure all schema files from Autobot are cached."""

    for name, fname in PROPERTIES.items():
        url = f"{BASE_URL}/properties/{name}"
        _ensure_file(CACHE_DIR / fname, url, refresh)

    for char in CLASS_CHARS:
        url = f"{BASE_URL}/properties/craftWeaponsByClass/{char}"
        dest = CACHE_DIR / "craft_by_class" / f"{char}.json"
        _ensure_file(dest, url, refresh)

    for ver, fname in GRADE_FILES.items():
        url = f"{BASE_URL}/getItemGrade/{ver}"
        _ensure_file(CACHE_DIR / fname, url, refresh)

    for fname, endpoint in BASE_ENDPOINTS.items():
        url = f"{BASE_URL}{endpoint}"
        _ensure_file(CACHE_DIR / fname, url, refresh)


def get_item_grade(defindex: int | str) -> Dict[str, Any]:
    """Return item grade data for a defindex, fetching if needed."""

    path = CACHE_DIR / "item_grade_by_defindex" / f"{defindex}.json"
    if not path.exists():
        url = f"{BASE_URL}/getItemGrade/fromDefindex/{defindex}"
        _ensure_file(path, url, refresh=False)
    with path.open() as f:
        return json.load(f)
