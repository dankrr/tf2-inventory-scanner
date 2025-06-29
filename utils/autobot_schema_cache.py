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
    "strangeParts": "strangeParts.json",
    "craftWeapons": "craftWeapons.json",
    "uncraftWeapons": "uncraftWeapons.json",
}

CLASS_NAMES = [
    "Scout",
    "Soldier",
    "Demo",
    "Pyro",
    "Medic",
    "Heavy",
    "Sniper",
    "Spy",
    "Engineer",
]

GRADE_FILES = {
    "v1": "item_grade_v1.json",
    "v2": "item_grade_v2.json",
}

BASE_ENDPOINTS = {
    "tf2schema.json": "/schema",
    "items_game.json": "/raw/items_game/cleaned",
}


def _fetch_json(url: str) -> Dict[str, Any]:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def _ensure_file(path: Path, url: str, refresh: bool) -> None:
    """Download ``url`` to ``path`` if ``refresh`` is True."""

    if refresh:
        data = _fetch_json(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        logger.info("\N{CHECK MARK} Cached %s", path)
    elif not path.exists():
        raise RuntimeError(f"Missing {path}. Run with --refresh to download.")


def ensure_all_cached(refresh: bool = False) -> None:
    """Ensure all schema files from Autobot are cached."""

    if refresh:
        legacy = Path("data/tf2schema.json")
        if legacy.exists():
            legacy.unlink()

    for name, fname in PROPERTIES.items():
        url = f"{BASE_URL}/properties/{name}"
        _ensure_file(CACHE_DIR / fname, url, refresh)

    for name in CLASS_NAMES:
        url = f"{BASE_URL}/properties/craftWeaponsByClass/{name}"
        dest = CACHE_DIR / f"craftWeaponsByClass_{name}.json"
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
