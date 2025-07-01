import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

from utils.local_data import DEFAULT_ITEMS_GAME_FILE, clean_items_game

import requests
import vdf

logger = logging.getLogger(__name__)

RAW_FILE = Path("cache/items_game.txt")
JSON_FILE = Path("cache/items_game.json")
CLEANED_FILE = DEFAULT_ITEMS_GAME_FILE
TTL = 48 * 60 * 60  # 48 hours

ITEMS_GAME: Dict[str, Any] | None = None
ITEM_BY_DEFINDEX: Dict[str, Any] = {}
KILLSTREAK_BY_ID: Dict[str, Any] = {}
PARSE_MS: int = 0
_ITEMS_GAME_FUTURE: asyncio.Future | None = None


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


def build_items_game_cleaned(force: bool = False) -> Dict[str, Any]:
    """Return a cleaned defindex map, downloading raw file if needed."""

    if force or not RAW_FILE.exists():
        url = "https://raw.githubusercontent.com/SteamDatabase/GameTracking-TF2/refs/heads/master/tf/scripts/items/items_game.txt"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        RAW_FILE.parent.mkdir(parents=True, exist_ok=True)
        RAW_FILE.write_text(r.text)
        text = r.text
    else:
        text = RAW_FILE.read_text()

    cleaned = clean_items_game(text)
    CLEANED_FILE.parent.mkdir(parents=True, exist_ok=True)
    CLEANED_FILE.write_text(json.dumps(cleaned))
    return cleaned


def _populate_maps(data: Dict[str, Any]) -> None:
    """Populate fast lookup dictionaries for items and killstreaks."""
    ITEM_BY_DEFINDEX.clear()
    KILLSTREAK_BY_ID.clear()
    for idx, meta in data.get("items", {}).items():
        ITEM_BY_DEFINDEX[str(idx)] = meta
    for attr_id, info in data.get("attributes", {}).items():
        name = str(info.get("name", "")).lower()
        if "killstreak" in name:
            KILLSTREAK_BY_ID[str(attr_id)] = info


def ensure_items_game_cached() -> Dict[str, Any]:
    """Return cached items_game data as a dict."""
    global ITEMS_GAME, PARSE_MS
    if JSON_FILE.exists():
        age = time.time() - JSON_FILE.stat().st_mtime
        if age < TTL:
            with JSON_FILE.open() as f:
                ITEMS_GAME = json.load(f)
            _populate_maps(ITEMS_GAME)
            logger.info(
                "items_game cache HIT: %s items",
                len(ITEMS_GAME.get("items", {})),
            )
            return ITEMS_GAME
    start = time.perf_counter()
    ITEMS_GAME = update_items_game()
    PARSE_MS = int((time.perf_counter() - start) * 1000)
    _populate_maps(ITEMS_GAME)
    logger.info(
        "items_game cache MISS, fetched %s items",
        len(ITEMS_GAME.get("items", {})),
    )
    logger.info("schema ready")
    logger.info("items_game_parse_ms=%s", PARSE_MS)
    return ITEMS_GAME


def ensure_future(loop: asyncio.AbstractEventLoop | None = None) -> asyncio.Future:
    """Return a future that loads items_game in the background."""
    global _ITEMS_GAME_FUTURE
    if _ITEMS_GAME_FUTURE is None:
        if loop is None:
            loop = asyncio.get_event_loop()
        _ITEMS_GAME_FUTURE = loop.create_task(
            asyncio.to_thread(ensure_items_game_cached)
        )
    return _ITEMS_GAME_FUTURE


async def wait_until_ready(timeout: float = 10.0) -> None:
    """Await the items_game cache, falling back on existing file if needed."""
    fut = ensure_future()
    try:
        await asyncio.wait_for(fut, timeout=timeout)
    except Exception as exc:  # pragma: no cover - network failure
        logger.info("items_game load failed: %s", exc)
        if JSON_FILE.exists() and not ITEM_BY_DEFINDEX:
            with JSON_FILE.open() as f:
                cached = json.load(f)
            _populate_maps(cached)
            logger.info("Using previous item schema")


def load_items_game_cleaned(force_rebuild: bool = False) -> Dict[str, Any]:
    """Load cleaned items_game into ``ITEM_BY_DEFINDEX`` and return the map."""

    global ITEM_BY_DEFINDEX

    path = CLEANED_FILE
    if not path.exists() or force_rebuild:
        data = build_items_game_cleaned(force=force_rebuild)
    else:
        with path.open() as f:
            data = json.load(f)

    if not isinstance(data, dict):
        data = {}

    ITEM_BY_DEFINDEX.clear()
    for idx, meta in data.items():
        ITEM_BY_DEFINDEX[str(idx)] = meta
    return ITEM_BY_DEFINDEX
