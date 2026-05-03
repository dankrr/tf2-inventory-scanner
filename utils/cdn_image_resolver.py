"""Resolve and cache Steam CDN icon hashes for TF2 variant items."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

STEAM_MARKET_APPID = "440"
STEAM_MARKET_CONTEXT_ID = "2"
CDN_BASE = "https://community.cloudflare.steamstatic.com/economy/image"
CDN_SIZE_SUFFIX = "/360fx360f"
DEFAULT_CACHE_PATH = Path("cache/cdn_images.json")


def is_enabled() -> bool:
    """Return ``True`` when CDN variant image resolution is enabled."""

    return os.getenv("CDN_RESOLVER_ENABLED", "1") != "0"


def build_market_hash_name(
    *,
    is_australium: bool,
    is_war_paint_tool: bool,
    item_name: str,
    paintkit_name: str | None,
    wear_name: str | None,
) -> str | None:
    """Build a Steam Market hash name for supported variant image lookups."""

    if is_australium:
        return f"Strange Australium {item_name}"
    if paintkit_name and wear_name and is_war_paint_tool:
        return f"{paintkit_name} War Paint ({wear_name})"
    if paintkit_name and wear_name:
        return f"{paintkit_name} {item_name} ({wear_name})"
    return None


def build_cache_key(item: dict[str, Any]) -> str | None:
    """Return deterministic cache key for supported variants, or ``None``."""

    defindex = item.get("defindex")
    paintkit_id = item.get("paintkit_id")
    wear_id = item.get("wear_id")

    if item.get("is_australium") and defindex is not None:
        return f"aus:{defindex}"
    if (
        item.get("is_war_paint_tool")
        and paintkit_id is not None
        and wear_id is not None
    ):
        return f"wpt:{paintkit_id}:{wear_id}"
    if (
        item.get("paintkit_id") is not None
        and wear_id is not None
        and defindex is not None
    ):
        return f"wp:{defindex}:{paintkit_id}:{wear_id}"
    return None


class CDNImageResolver:
    """Resolve Steam icon hashes for item variants and persist successful lookups."""

    def __init__(self, cache_path: Path = DEFAULT_CACHE_PATH) -> None:
        self.cache_path = cache_path
        self._cache: dict[str, str] = self._load_cache()

    def _load_cache(self) -> dict[str, str]:
        if not self.cache_path.exists():
            return {}
        try:
            with self.cache_path.open() as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except Exception:
            logger.exception("Failed to read CDN cache")
        return {}

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.cache_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._cache, indent=2))
        tmp.replace(self.cache_path)

    @staticmethod
    def build_cdn_url(icon_hash: str) -> str:
        """Return full CDN URL from an ``icon_url`` hash."""

        return f"{CDN_BASE}/{icon_hash}{CDN_SIZE_SUFFIX}"

    async def resolve_hash(self, market_hash_name: str) -> str | None:
        """Return Steam ``icon_url`` hash for ``market_hash_name`` or ``None``."""

        endpoint = (
            "https://steamcommunity.com/market/listings/440/"
            f"{quote(market_hash_name, safe='')}/render/?count=1&currency=1&format=json"
        )
        timeout = httpx.Timeout(8.0)
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(endpoint)
                if response.status_code == 429:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                if response.status_code != 200:
                    return None
                payload = response.json()
                assets = (
                    payload.get("assets", {})
                    .get(STEAM_MARKET_APPID, {})
                    .get(STEAM_MARKET_CONTEXT_ID, {})
                )
                if not isinstance(assets, dict) or not assets:
                    return None
                first_asset = next(iter(assets.values()))
                if not isinstance(first_asset, dict):
                    return None
                icon_hash = first_asset.get("icon_url")
                return str(icon_hash) if icon_hash else None
            except Exception:
                if attempt == 2:
                    return None
                await asyncio.sleep(0.5 * (2**attempt))
        return None

    async def resolve_item_image(self, item: dict[str, Any]) -> str | None:
        """Resolve a full CDN image URL for a supported variant item."""

        cache_key = build_cache_key(item)
        if not cache_key:
            return None
        cached_hash = self._cache.get(cache_key)
        if cached_hash:
            return self.build_cdn_url(cached_hash)

        market_hash_name = build_market_hash_name(
            is_australium=bool(item.get("is_australium")),
            is_war_paint_tool=bool(item.get("is_war_paint_tool")),
            item_name=str(item.get("base_name") or item.get("item_name") or "").strip(),
            paintkit_name=item.get("paintkit_name"),
            wear_name=item.get("wear_name"),
        )
        if not market_hash_name:
            return None

        icon_hash = await self.resolve_hash(market_hash_name)
        if not icon_hash:
            return None
        self._cache[cache_key] = icon_hash
        self._save_cache()
        return self.build_cdn_url(icon_hash)


__all__ = [
    "CDNImageResolver",
    "build_cache_key",
    "build_market_hash_name",
    "is_enabled",
]
