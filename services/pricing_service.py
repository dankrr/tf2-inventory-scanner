import logging
import os
import time
from pathlib import Path
from typing import Any, Dict

import requests

from utils.cache_manager import read_json, write_json

logger = logging.getLogger(__name__)

PRICE_CACHE_FILE = Path("data/cached_prices.json")
CURRENCY_FILE = Path("data/cached_currencies.json")
TTL = 48 * 60 * 60  # 48 hours

PRICES: Dict[str, Any] | None = None
KEY_REF_RATE: float | None = None


def _parse_prices(payload: Dict[str, Any]) -> Dict[str, Any]:
    items: Dict[str, Any] = {}
    resp = payload.get("response", {})
    for data in resp.get("items", {}).values():
        defs = data.get("defindex") or []
        if not isinstance(defs, list):
            defs = [defs]
        prices = data.get("prices", {})
        for q, qinfo in prices.items():
            trade = qinfo.get("Tradable") or next(iter(qinfo.values()), {})
            craft = trade.get("0") or next(iter(trade.values()), {})
            value = craft.get("value")
            currency = craft.get("currency", "metal")
            last_update = craft.get("last_update", 0)
            for d in defs:
                sku = f"{d};{q}"
                items[sku] = {
                    "defindex": int(d),
                    "quality": int(q),
                    "value": value,
                    "currency": currency,
                    "last_update": last_update,
                }
    return items


def _fetch_prices(api_key: str) -> Dict[str, Any]:
    url = "https://backpack.tf/api/IGetPrices/v4?key=" f"{api_key}&compress=1"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    payload = r.json()
    return _parse_prices(payload)


def _fetch_currencies(api_key: str) -> Dict[str, Any]:
    url = f"https://backpack.tf/api/IGetCurrencies/v1?key={api_key}&appid=440"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json().get("response", {})
    return data.get("currencies", {})


def ensure_price_cache(api_key: str | None = None) -> Dict[str, Any]:
    global PRICES
    if PRICES is not None:
        return PRICES
    if api_key is None:
        api_key = os.getenv("BACKPACK_API_KEY")
    if not api_key:
        raise ValueError("BACKPACK_API_KEY is required to fetch prices")

    if PRICE_CACHE_FILE.exists():
        age = time.time() - PRICE_CACHE_FILE.stat().st_mtime
        if age < TTL:
            PRICES = read_json(PRICE_CACHE_FILE)
            logger.info("Price cache HIT: %s entries", len(PRICES))
            return PRICES

    fetched = _fetch_prices(api_key)
    write_json(PRICE_CACHE_FILE, fetched)
    PRICES = fetched
    logger.info("Price cache MISS, fetched %s entries", len(PRICES))
    return PRICES


def ensure_currency_rates(api_key: str | None = None) -> float:
    global KEY_REF_RATE
    if KEY_REF_RATE is not None:
        return KEY_REF_RATE
    if api_key is None:
        api_key = os.getenv("BACKPACK_API_KEY")
    if not api_key:
        raise ValueError("BACKPACK_API_KEY is required to fetch currency rates")

    if CURRENCY_FILE.exists():
        currencies = read_json(CURRENCY_FILE)
        metal_val = currencies.get("metal", {}).get("value")
        key_val = currencies.get("keys", {}).get("value")
        if metal_val and key_val:
            KEY_REF_RATE = key_val / metal_val
            return KEY_REF_RATE

    currencies = _fetch_currencies(api_key)
    write_json(CURRENCY_FILE, currencies)

    metal_val = currencies.get("metal", {}).get("value")
    key_val = currencies.get("keys", {}).get("value")
    KEY_REF_RATE = key_val / metal_val if metal_val else 0.0
    return KEY_REF_RATE


def convert_value(value: float, key_ref_rate: float) -> tuple[int, float]:
    keys = int(value / key_ref_rate) if key_ref_rate else 0
    refs = round((value % key_ref_rate) / 100, 2) if key_ref_rate else 0.0
    return keys, refs


def format_price(value: float, key_ref_rate: float) -> str:
    keys, refs = convert_value(value, key_ref_rate)
    parts = []
    if keys:
        parts.append(f"{keys} key{'s' if keys != 1 else ''}")
    if refs:
        parts.append(f"{refs:.2f} ref")
    if not parts:
        return "0.00 ref"
    return " ".join(parts)
