import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

import requests
import vdf

logger = logging.getLogger(__name__)

TXT_FILE = Path("cache/items_game.txt")
JSON_FILE = Path("cache/items_game.json")
TTL = 24 * 60 * 60  # 24 hours

ITEMS_GAME: Dict[str, Any] | None = None


def _fetch_items_game() -> Dict[str, Any]:
    """Download and parse items_game.txt from SteamDatabase."""
    url = (
        "https://raw.githubusercontent.com/SteamDatabase/GameTracking-TF2/master/"
        "tf/scripts/items/items_game.txt"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    text = r.text
    TXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    TXT_FILE.write_text(text)
    data = vdf.loads(text)
    JSON_FILE.write_text(json.dumps(data))
    return data


def ensure_items_game_cached() -> Dict[str, Any]:
    """Return cached items_game data as a dict."""
    global ITEMS_GAME
    if JSON_FILE.exists():
        age = time.time() - JSON_FILE.stat().st_mtime
        if age < TTL:
            ITEMS_GAME = json.loads(JSON_FILE.read_text())
            logger.info(
                "items_game cache HIT: %s items",
                len(ITEMS_GAME.get("items", {})),
            )
            return ITEMS_GAME
    ITEMS_GAME = _fetch_items_game()
    logger.info(
        "items_game cache MISS, fetched %s items",
        len(ITEMS_GAME.get("items", {})),
    )
    return ITEMS_GAME
