from __future__ import annotations

from typing import Any, Dict, Tuple

from . import local_data
from .price_loader import (
    ensure_prices_cached,
    build_price_map,
    load_price_map,
    dump_price_map,
    PRICE_MAP_FILE,
)
from .price_service import format_price


_default_service: ValuationService | None = None


def get_valuation_service() -> "ValuationService":
    """Return singleton :class:`ValuationService` instance."""
    global _default_service
    if _default_service is None:
        try:
            _default_service = ValuationService()
        except Exception:  # pragma: no cover - fallback when prices unavailable
            _default_service = ValuationService(price_map={})
    return _default_service


class ValuationService:
    """Wrapper around name-based price lookups."""

    def __init__(
        self,
        price_map: (
            Dict[Tuple[str, int, bool, bool, int, int], Dict[str, Any]] | None
        ) = None,
    ) -> None:
        if price_map is None:
            prices_path = ensure_prices_cached()
            use_cache = False
            if PRICE_MAP_FILE.exists():
                try:
                    if PRICE_MAP_FILE.stat().st_mtime >= prices_path.stat().st_mtime:
                        price_map = load_price_map(PRICE_MAP_FILE)
                        use_cache = True
                except Exception:
                    use_cache = False
            if not use_cache:
                price_map = build_price_map(prices_path)
                dump_price_map(price_map, PRICE_MAP_FILE)
        self.price_map = price_map

    def get_price_info(
        self,
        item_name: str,
        quality: int,
        craftable: bool = True,
        is_australium: bool = False,
        effect_id: int | None = None,
        killstreak_tier: int | None = None,
    ) -> Dict[str, Any] | None:
        """Return raw price info dict for the item if available."""
        key = (
            item_name,
            quality,
            craftable,
            is_australium,
            effect_id or 0,
            killstreak_tier or 0,
        )
        info = self.price_map.get(key)
        if info is None and killstreak_tier is not None:
            info = self.price_map.get(
                (
                    item_name,
                    quality,
                    craftable,
                    is_australium,
                    effect_id or 0,
                    0,
                )
            )
        if info is None and effect_id is not None:
            info = self.price_map.get(
                (
                    item_name,
                    quality,
                    craftable,
                    is_australium,
                    0,
                    killstreak_tier or 0,
                )
            )
        return info

    def format_price(
        self,
        item_name: str,
        quality: int,
        craftable: bool = True,
        is_australium: bool = False,
        *,
        effect_id: int | None = None,
        killstreak_tier: int | None = None,
        currencies: Dict[str, Any] | None = None,
    ) -> str:
        """Return formatted price string using Backpack.tf key price."""
        info = self.get_price_info(
            item_name,
            quality,
            craftable,
            is_australium,
            effect_id,
            killstreak_tier,
        )
        if not info:
            return ""
        value = info.get("value_raw")
        if value is None:
            return ""
        if currencies is None:
            currencies = local_data.CURRENCIES
        return format_price(value, currencies)
