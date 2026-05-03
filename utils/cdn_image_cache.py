"""Persistent cache for Steam CDN image icon hashes."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

CDN_IMAGES_FILE = Path("cache/cdn_images.json")

# In-memory cache: {cache_key: icon_url_hash}
_cache: Dict[str, str] = {}
_loaded = False


def _ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    if CDN_IMAGES_FILE.exists():
        try:
            data = json.loads(CDN_IMAGES_FILE.read_text())
            if isinstance(data, dict):
                _cache.update(data)
        except Exception as exc:
            logger.warning("Failed to load CDN image cache: %s", exc)


def get(cache_key: str) -> str | None:
    """Return the cached icon_url hash for ``cache_key``, or None if not cached."""
    _ensure_loaded()
    return _cache.get(cache_key)


def put(cache_key: str, icon_hash: str) -> None:
    """Store ``icon_hash`` for ``cache_key`` and persist to disk atomically."""
    _ensure_loaded()
    _cache[cache_key] = icon_hash
    _save()


def _save() -> None:
    try:
        CDN_IMAGES_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CDN_IMAGES_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(_cache, indent=2))
        tmp.replace(CDN_IMAGES_FILE)
    except Exception as exc:
        logger.warning("Failed to save CDN image cache: %s", exc)


def clear() -> None:
    """Remove the on-disk cache file and reset the in-memory cache."""
    global _loaded
    _cache.clear()
    _loaded = False
    try:
        if CDN_IMAGES_FILE.exists():
            CDN_IMAGES_FILE.unlink()
    except Exception as exc:
        logger.warning("Failed to clear CDN image cache: %s", exc)


def cache_key_australium(defindex: int) -> str:
    return f"aus:{defindex}"


def cache_key_war_painted(defindex: int, paintkit_id: int, wear_id: int) -> str:
    return f"wp:{defindex}:{paintkit_id}:{wear_id}"


def cache_key_war_paint_tool(paintkit_id: int, wear_id: int) -> str:
    return f"wpt:{paintkit_id}:{wear_id}"


__all__ = [
    "CDN_IMAGES_FILE",
    "get",
    "put",
    "clear",
    "cache_key_australium",
    "cache_key_war_painted",
    "cache_key_war_paint_tool",
]
