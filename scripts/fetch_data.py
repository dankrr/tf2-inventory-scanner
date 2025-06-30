import json
import logging
from pathlib import Path
from typing import List

import requests

logger = logging.getLogger(__name__)

AUTOBOT_BASE = "https://schema.autobot.tf"
ITEMS_GAME_URL = (
    "https://raw.githubusercontent.com/SteamDatabase/GameTracking-TF2/"
    "master/tf/resource/tf2_base/items_game.txt"
)

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


def fetch_items_game() -> Path:
    """Download items_game.txt and return its path."""

    resp = requests.get(ITEMS_GAME_URL, timeout=30)
    resp.raise_for_status()
    CACHE_DIR.mkdir(exist_ok=True)
    dest = CACHE_DIR / "items_game.txt"
    dest.write_text(resp.text)
    logger.info("Downloaded items_game.txt -> %s", dest)
    return dest


def fetch_autobot_schema() -> Path:
    """Download tf2_schema.json from AutoBot."""

    resp = requests.get(f"{AUTOBOT_BASE}/schema", timeout=20)
    resp.raise_for_status()
    CACHE_DIR.mkdir(exist_ok=True)
    dest = CACHE_DIR / "tf2_schema.json"
    dest.write_text(json.dumps(resp.json()))
    logger.info("Downloaded schema -> %s", dest)
    return dest


def fetch_autobot_properties() -> List[Path]:
    """Download property files from AutoBot and return their paths."""

    paths: List[Path] = []
    for name in PROPERTIES:
        resp = requests.get(f"{AUTOBOT_BASE}/properties/{name}", timeout=20)
        resp.raise_for_status()
        path = CACHE_DIR / f"{name}.json"
        path.write_text(json.dumps(resp.json()))
        logger.info("Downloaded %s -> %s", name, path)
        paths.append(path)
    return paths


def refresh_all() -> None:
    """Refresh all cached files."""

    fetch_items_game()
    fetch_autobot_schema()
    fetch_autobot_properties()


__all__ = [
    "fetch_items_game",
    "fetch_autobot_schema",
    "fetch_autobot_properties",
    "refresh_all",
]
