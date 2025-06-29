import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

JSON_FILE = Path("cache/items_game.json")
TTL = 48 * 60 * 60  # 48 hours

ITEMS_GAME: Dict[str, Any] | None = None
ITEM_BY_DEFINDEX: Dict[str, Any] = {}
KILLSTREAK_BY_ID: Dict[str, Any] = {}
PARSE_MS: int = 0
_ITEMS_GAME_FUTURE: asyncio.Future | None = None


def update_items_game() -> Dict[str, Any]:
    """Download the cleaned items_game from schema.autobot.tf."""

    url = "https://schema.autobot.tf/raw/items_game/cleaned"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()

    JSON_FILE.parent.mkdir(parents=True, exist_ok=True)
    JSON_FILE.write_text(json.dumps(data))
    return data


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
