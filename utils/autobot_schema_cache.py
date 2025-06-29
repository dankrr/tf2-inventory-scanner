import json
import logging
from pathlib import Path
from typing import Any, Dict

import requests
from . import items_game_cache

logger = logging.getLogger(__name__)

BASE_URL = "https://schema.autobot.tf"
CACHE_DIR = Path("cache")
SCHEMA_DIR = CACHE_DIR / "schema"
ITEMS_GAME_DIR = CACHE_DIR / "items_game"
PROPERTIES_DIR = CACHE_DIR / "properties"
GRADES_DIR = CACHE_DIR / "grades"

SCHEMA_KEYS = [
    "qualities",
    "qualityNames",
    "originNames",
    "attributes",
    "item_sets",
    "attribute_controlled_attached_particles",
    "item_levels",
    "kill_eater_score_types",
    "string_lookups",
    "items",
    "paintkits",
]

ITEMS_GAME_KEYS = [
    "items",
    "attributes",
    "item_sets",
    "item_levels",
    "kill_eater_score_types",
    "string_lookups",
    "attribute_controlled_attached_particles",
    "armory_data",
    "item_criteria_templates",
    "random_attribute_templates",
    "lootlist_job_template_definitions",
    "client_loot_lists",
    "revolving_loot_lists",
    "recipes",
    "achievement_rewards",
    "mvm_maps",
    "mvm_tours",
    "matchmaking_categories",
    "maps",
    "master_maps_list",
    "steam_packages",
    "community_market_item_remaps",
    "war_definitions",
    "game_info",
    "qualities",
    "colors",
    "rarities",
    "equip_regions_list",
    "equip_conflicts",
    "quest_objective_conditions",
    "item_series_types",
    "item_collections",
    "operations",
    "prefabs",
]

PROPERTIES_KEYS = [
    "defindexes",
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

CLASS_NAMES = [
    "Scout",
    "Soldier",
    "Pyro",
    "Demoman",
    "Heavy",
    "Engineer",
    "Medic",
    "Sniper",
    "Spy",
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


GRADE_ENDPOINTS = [
    "v1",
    "v2",
]


def _fetch_json(url: str) -> Dict[str, Any]:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def _ensure_file(path: Path, url: str, refresh: bool) -> None:
    """Download ``url`` to ``path`` if ``refresh`` is True."""

    if refresh:
        try:
            data = _fetch_json(url)
        except requests.HTTPError as exc:  # pragma: no cover - network failure
            if exc.response is not None and exc.response.status_code == 404:
                logger.warning("%s returned 404; skipping", url)
                return
            raise
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

    for name in PROPERTIES_KEYS:
        url = f"{BASE_URL}/properties/{name}"
        dest = PROPERTIES_DIR / f"{name}.json"
        _ensure_file(dest, url, refresh)

    fetched_classes = []
    for name in CLASS_NAMES:
        canonical = _canonical_class(name)
        if not canonical:
            logger.warning("Unknown class %s; skipping", name)
            continue
        url = f"{BASE_URL}/properties/craftWeaponsByClass/{canonical}"
        dest = PROPERTIES_DIR / f"craftWeaponsByClass_{canonical}.json"
        _ensure_file(dest, url, refresh)
        fetched_classes.append(canonical)

    if refresh and fetched_classes:
        logger.info("craftWeaponsByClass fetched for: %s", ", ".join(fetched_classes))

    for endpoint in GRADE_ENDPOINTS:
        url = f"{BASE_URL}/getItemGrade/{endpoint}"
        dest = GRADES_DIR / f"{endpoint}.json"
        _ensure_file(dest, url, refresh)

    for key in SCHEMA_KEYS:
        url = f"{BASE_URL}/raw/schema/{key}"
        dest = SCHEMA_DIR / f"{key}.json"
        _ensure_file(dest, url, refresh)

    for key in ITEMS_GAME_KEYS:
        url = f"{BASE_URL}/raw/items_game/{key}"
        dest = ITEMS_GAME_DIR / f"{key}.json"
        try:
            _ensure_file(dest, url, refresh)
        except requests.HTTPError as e:  # pragma: no cover - network failure
            print(f"[!] Failed to fetch {url}: {e}")

    if refresh:
        items_game_cache.update_items_game()
    elif not items_game_cache.JSON_FILE.exists():
        raise RuntimeError(
            f"Missing {items_game_cache.JSON_FILE}. Run with --refresh to download."
        )


def get_item_grade(defindex: int | str) -> Dict[str, Any]:
    """Return item grade data for a defindex, fetching if needed."""

    path = GRADES_DIR / "fromDefindex" / f"{defindex}.json"
    if not path.exists():
        url = f"{BASE_URL}/getItemGrade/fromDefindex/{defindex}"
        _ensure_file(path, url, refresh=False)
    with path.open() as f:
        return json.load(f)
