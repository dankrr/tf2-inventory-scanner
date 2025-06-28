import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

PRICE_CACHE_FILE = Path("data/price_cache.json")
CURRENCY_FILE = Path("data/currency_rates.json")
TTL = 6 * 60 * 60  # 6 hours

PRICES: Dict[str, Any] | None = None
KEY_REF_RATE: float | None = None


def _fetch_prices(api_key: str) -> Dict[str, Any]:
    url = "https://backpack.tf/api/IGetPrices/v4?key=" f"{api_key}&compress=1&appid=440"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json().get("response", {})
    if data.get("success") != 1:
        raise ValueError("Invalid response from backpack.tf")

    items: Dict[str, Any] = {}
    for sku, info in data.get("items", {}).items():
        entry = {
            "defindex": info.get("defindex"),
            "quality": info.get("quality"),
            "value": info.get("value"),
            "currency": info.get("currency"),
            "last_update": info.get("last_update"),
        }
        if "value_high" in info:
            entry["value_high"] = info["value_high"]
        items[sku] = entry
    return items


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
            with PRICE_CACHE_FILE.open() as f:
                PRICES = json.load(f)
            logger.info("Price cache HIT: %s entries", len(PRICES))
            return PRICES

    fetched = _fetch_prices(api_key)
    PRICE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PRICE_CACHE_FILE.open("w") as f:
        json.dump(fetched, f)
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
        with CURRENCY_FILE.open() as f:
            currencies = json.load(f)
        metal_val = currencies.get("metal", {}).get("value")
        key_val = currencies.get("keys", {}).get("value")
        if metal_val and key_val:
            KEY_REF_RATE = key_val / metal_val
            return KEY_REF_RATE

    currencies = _fetch_currencies(api_key)
    CURRENCY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CURRENCY_FILE.open("w") as f:
        json.dump(currencies, f)

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
