"""Backpack.tf price caching utilities."""

from __future__ import annotations

import os
import json
import time
import logging
from pathlib import Path
from typing import Any, Dict

import requests

PRICE_TTL = 48 * 60 * 60  # refresh every other day
CACHE_DIR = Path("data")
PRICE_CACHE = CACHE_DIR / "backpack_prices.json"
CURR_CACHE = CACHE_DIR / "backpack_currencies.json"

logger = logging.getLogger(__name__)

PRICES_RAW: Dict[str, Any] | None = None
CURRENCIES: Dict[str, Any] | None = None
KEY_RATE: float | None = None


def _parse_prices(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    items: dict[str, dict] = {}
    response = payload.get("response", {})
    for info in response.get("items", {}).values():
        defindexes = info.get("defindex") or []
        if not isinstance(defindexes, list):
            defindexes = [defindexes]
        prices = info.get("prices", {})
        for q, qinfo in prices.items():
            trade = qinfo.get("Tradable") or next(iter(qinfo.values()), {})
            craft = trade.get("0") or next(iter(trade.values()), {})
            value = craft.get("value")
            currency = craft.get("currency", "metal")
            last_update = craft.get("last_update", 0)
            for d in defindexes:
                sku = f"{d};{q}"
                items[sku] = {
                    "defindex": int(d),
                    "quality": int(q),
                    "value": value,
                    "currency": currency,
                    "last_update": last_update,
                }
    return items


def _fetch_json(url: str) -> Dict[str, Any]:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def ensure_prices_cached() -> Dict[str, Any]:
    """Load or refresh item price cache."""

    global PRICES_RAW

    if PRICES_RAW is not None:
        return PRICES_RAW

    api_key = os.getenv("BACKPACK_API_KEY")
    if not api_key:
        raise RuntimeError("BACKPACK_API_KEY not set")

    fresh = (
        PRICE_CACHE.exists() and time.time() - PRICE_CACHE.stat().st_mtime < PRICE_TTL
    )
    if fresh:
        try:
            with PRICE_CACHE.open() as f:
                PRICES_RAW = json.load(f)
            logger.info("Price cache HIT: %s entries", len(PRICES_RAW))
            return PRICES_RAW
        except Exception:
            logger.warning("Price cache malformed, refetching")

    try:
        payload = _fetch_json(
            f"https://backpack.tf/api/IGetPrices/v4?key={api_key}&compress=1"
        )
        PRICES_RAW = _parse_prices(payload)
        PRICE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with PRICE_CACHE.open("w") as f:
            json.dump(PRICES_RAW, f)
        logger.info("Fetched prices: %s entries", len(PRICES_RAW))
    except Exception as exc:
        logger.error("Price fetch failed: %s", exc)
        if PRICE_CACHE.exists():
            with PRICE_CACHE.open() as f:
                PRICES_RAW = json.load(f)
            logger.warning("Using cached price data (%s entries)", len(PRICES_RAW))
        else:
            raise RuntimeError("No price data available") from exc

    return PRICES_RAW


def ensure_currencies_cached() -> Dict[str, Any]:
    """Load or refresh currency rates."""

    global CURRENCIES, KEY_RATE

    if CURRENCIES is not None:
        return CURRENCIES

    api_key = os.getenv("BACKPACK_API_KEY")
    if not api_key:
        raise RuntimeError("BACKPACK_API_KEY not set")

    fresh = CURR_CACHE.exists() and time.time() - CURR_CACHE.stat().st_mtime < PRICE_TTL
    if fresh:
        try:
            with CURR_CACHE.open() as f:
                CURRENCIES = json.load(f)
            logger.info("Currency cache HIT")
        except Exception:
            logger.warning("Currency cache malformed, refetching")
            CURRENCIES = None

    if CURRENCIES is None:
        try:
            payload = _fetch_json(
                f"https://backpack.tf/api/IGetCurrencies/v1?key={api_key}"
            )
            CURRENCIES = payload.get("response", {}).get("currencies", {})
            CURR_CACHE.parent.mkdir(parents=True, exist_ok=True)
            with CURR_CACHE.open("w") as f:
                json.dump(CURRENCIES, f)
            logger.info("Fetched currency rates")
        except Exception as exc:
            logger.error("Currency fetch failed: %s", exc)
            if CURR_CACHE.exists():
                with CURR_CACHE.open() as f:
                    CURRENCIES = json.load(f)
                logger.warning("Using cached currency data")
            else:
                raise RuntimeError("No currency data available") from exc

    metal_val = CURRENCIES.get("metal", {}).get("value")
    key_val = CURRENCIES.get("keys", {}).get("value")
    KEY_RATE = key_val / metal_val if metal_val else 0.0
    return CURRENCIES


def get_price_for_sku(sku: str) -> str:
    """Return formatted price for the given SKU."""

    if PRICES_RAW is None:
        ensure_prices_cached()
    if KEY_RATE is None:
        ensure_currencies_cached()

    price = PRICES_RAW.get(sku) if PRICES_RAW else None
    if not price:
        return "Unknown Value"

    value = price.get("value", 0)
    currency = price.get("currency", "metal")

    if currency == "keys":
        keys = int(value)
        ref = round((value - keys) * KEY_RATE, 2)
    else:
        keys = int(value // KEY_RATE) if KEY_RATE else 0
        ref = round(value - keys * KEY_RATE, 2)

    parts = []
    if keys:
        parts.append(f"{keys} key{'s' if keys != 1 else ''}")
    if ref:
        parts.append(f"{ref:.2f} ref")
    if not parts:
        return "0 ref"
    return " ".join(parts)
