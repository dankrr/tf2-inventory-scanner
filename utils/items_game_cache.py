import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

import requests
import vdf

logger = logging.getLogger(__name__)

RAW_FILE = Path("cache/items_game_raw.txt")
JSON_FILE = Path("cache/items_game.json")
TTL = 48 * 60 * 60  # 48 hours

ITEMS_GAME: Dict[str, Any] | None = None


def update_items_game() -> Dict[str, Any]:
    """Download, filter and cache items_game from SteamDatabase."""

    url = (
        "https://raw.githubusercontent.com/SteamDatabase/GameTracking-TF2/master/"
        "tf/scripts/items/items_game.txt"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    text = r.text
    RAW_FILE.parent.mkdir(parents=True, exist_ok=True)
    RAW_FILE.write_text(text)

    parsed = vdf.loads(text).get("items_game", {})
    allowed = ["items", "item_sets", "qualities", "rarities", "attributes"]
    reduced = {k: parsed.get(k, {}) for k in allowed if k in parsed}

    JSON_FILE.write_text(json.dumps(reduced))
    return reduced


def ensure_items_game_cached() -> Dict[str, Any]:
    """Return cached items_game data as a dict."""
    global ITEMS_GAME
    if JSON_FILE.exists():
        age = time.time() - JSON_FILE.stat().st_mtime
        if age < TTL:
            with JSON_FILE.open() as f:
                ITEMS_GAME = json.load(f)
            logger.info(
                "items_game cache HIT: %s items",
                len(ITEMS_GAME.get("items", {})),
            )
            return ITEMS_GAME
    ITEMS_GAME = update_items_game()
    logger.info(
        "items_game cache MISS, fetched %s items",
        len(ITEMS_GAME.get("items", {})),
    )
    return ITEMS_GAME
