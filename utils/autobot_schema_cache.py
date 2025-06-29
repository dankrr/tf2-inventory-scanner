import json
import logging
from pathlib import Path
from typing import Any, Dict

import requests
from . import items_game_cache

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

# Map various aliases to canonical TF2 class names used by the Autobot API.
CLASS_ALIASES = {
    "demo": "Demoman",
    "demoman": "Demoman",
    "pyro": "Pyro",
    "engie": "Engineer",
    "engineer": "Engineer",
    "heavy": "Heavy",
    "solly": "Soldier",
    "soldier": "Soldier",
    "scout": "Scout",
    "medic": "Medic",
    "sniper": "Sniper",
    "spy": "Spy",
}


def _canonical_class(name: str) -> str | None:
    """Return canonical TF2 class name or ``None`` if unknown."""

    return CLASS_ALIASES.get(name.lower())


GRADE_FILES = {
    "v1": "item_grade_v1.json",
    "v2": "item_grade_v2.json",
}

BASE_ENDPOINTS = {
    "tf2schema.json": "/schema",
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

    fetched_classes = []
    for name in CLASS_NAMES:
        canonical = _canonical_class(name)
        if not canonical:
            logger.warning("Unknown class %s; skipping", name)
            continue
        url = f"{BASE_URL}/properties/craftWeaponsByClass/{canonical}"
        dest = CACHE_DIR / f"craftWeaponsByClass_{canonical}.json"
        _ensure_file(dest, url, refresh)
        fetched_classes.append(canonical)

    if refresh and fetched_classes:
        logger.info("craftWeaponsByClass fetched for: %s", ", ".join(fetched_classes))

    for ver, fname in GRADE_FILES.items():
        url = f"{BASE_URL}/getItemGrade/{ver}"
        _ensure_file(CACHE_DIR / fname, url, refresh)

    for fname, endpoint in BASE_ENDPOINTS.items():
        url = f"{BASE_URL}{endpoint}"
        _ensure_file(CACHE_DIR / fname, url, refresh)

    if refresh:
        items_game_cache.update_items_game()
    elif not items_game_cache.JSON_FILE.exists():
        raise RuntimeError(
            f"Missing {items_game_cache.JSON_FILE}. Run with --refresh to download."
        )


def get_item_grade(defindex: int | str) -> Dict[str, Any]:
    """Return item grade data for a defindex, fetching if needed."""

    path = CACHE_DIR / "item_grade_by_defindex" / f"{defindex}.json"
    if not path.exists():
        url = f"{BASE_URL}/getItemGrade/fromDefindex/{defindex}"
        _ensure_file(path, url, refresh=False)
    with path.open() as f:
        return json.load(f)
