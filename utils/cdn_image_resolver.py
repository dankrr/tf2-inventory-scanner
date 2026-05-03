"""Resolve CDN image URLs for TF2 item variants from the Steam Market."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

CDN_BASE = "https://community.cloudflare.steamstatic.com/economy/image"
MARKET_RENDER_URL = (
    "https://steamcommunity.com/market/listings/440/{name}/render/"
    "?count=1&currency=1&format=json"
)
_MAX_RETRIES = 3
_SEMAPHORE: asyncio.Semaphore | None = None


def _semaphore() -> asyncio.Semaphore:
    global _SEMAPHORE
    if _SEMAPHORE is None:
        _SEMAPHORE = asyncio.Semaphore(4)
    return _SEMAPHORE


def build_market_hash_name(
    *,
    is_australium: bool = False,
    defindex: int | None = None,
    base_name: str | None = None,
    paintkit_name: str | None = None,
    wear_name: str | None = None,
    is_war_paint_tool: bool = False,
) -> str | None:
    """Return the Steam Market hash name for an item variant, or None if not applicable."""

    if is_australium and base_name:
        # Strip quality prefix — market uses "Strange Australium <weapon>"
        clean = re.sub(
            r"^(Strange|Unique|Vintage|Haunted|Collector's|Genuine|Unusual)\s+",
            "",
            base_name,
            flags=re.IGNORECASE,
        )
        return f"Strange Australium {clean}"

    if is_war_paint_tool and paintkit_name and wear_name:
        return f"{paintkit_name} War Paint ({wear_name})"

    if paintkit_name and base_name and wear_name:
        return f"{paintkit_name} {base_name} ({wear_name})"

    return None


def cdn_url(icon_hash: str) -> str:
    """Return the full CDN URL for a given icon hash."""
    return f"{CDN_BASE}/{icon_hash}/360fx360f"


async def _fetch_icon_hash(
    client: httpx.AsyncClient, market_hash_name: str
) -> str | None:
    """Fetch the icon_url hash from the Steam Market render endpoint."""

    url = MARKET_RENDER_URL.format(name=quote(market_hash_name))
    delay = 1.0

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            async with _semaphore():
                resp = await client.get(url, timeout=10)

            if resp.status_code == 429:
                logger.warning(
                    "Steam Market rate-limited for %r (attempt %d/%d)",
                    market_hash_name,
                    attempt,
                    _MAX_RETRIES,
                )
                # Don't cache 429 — just fail this cycle
                return None

            if resp.status_code == 404:
                logger.debug("Steam Market 404 for %r", market_hash_name)
                return None

            resp.raise_for_status()
            data: dict[str, Any] = resp.json()

            assets = data.get("assets", {})
            app_assets = assets.get("440", {}).get("2", {})
            for asset_data in app_assets.values():
                icon = asset_data.get("icon_url")
                if icon:
                    return icon

            logger.debug(
                "No icon_url in Steam Market response for %r", market_hash_name
            )
            return None

        except httpx.HTTPStatusError:
            return None
        except Exception as exc:
            logger.warning(
                "CDN resolver error for %r (attempt %d/%d): %s",
                market_hash_name,
                attempt,
                _MAX_RETRIES,
                exc,
            )
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(delay)
                delay *= 2

    return None


async def resolve_icon_hash(
    client: httpx.AsyncClient, market_hash_name: str
) -> str | None:
    """Return the Steam CDN icon_url hash for ``market_hash_name``, or None on failure."""
    try:
        return await _fetch_icon_hash(client, market_hash_name)
    except Exception as exc:  # never raise out of this module
        logger.warning(
            "Unexpected CDN resolver error for %r: %s", market_hash_name, exc
        )
        return None


def is_resolver_enabled() -> bool:
    """Return True unless CDN_RESOLVER_ENABLED is explicitly set to 0."""
    return os.getenv("CDN_RESOLVER_ENABLED", "1") != "0"


__all__ = [
    "build_market_hash_name",
    "cdn_url",
    "resolve_icon_hash",
    "is_resolver_enabled",
]
