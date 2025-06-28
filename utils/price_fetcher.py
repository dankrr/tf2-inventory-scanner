import os
import json
import time
import logging
import requests

PRICE_TTL = 48 * 60 * 60  # 48 hours
CACHE_DIR = "data"
PRICE_CACHE = f"{CACHE_DIR}/cached_prices.json"
CURR_CACHE = f"{CACHE_DIR}/cached_currencies.json"
KEY = os.getenv("BACKPACK_API_KEY")
if not KEY:
    raise RuntimeError("BACKPACK_API_KEY not set. Please set it in .env or export it.")

logger = logging.getLogger(__name__)


def ensure_prices_cached():
    if (
        os.path.exists(PRICE_CACHE)
        and time.time() - os.path.getmtime(PRICE_CACHE) < PRICE_TTL
    ):
        with open(PRICE_CACHE) as f:
            data = json.load(f)
        logger.info("Price cache HIT: %s entries", len(data))
        return data
    logger.info("Fetching prices from backpack.tf")
    url = f"https://backpack.tf/api/IGetPrices/v4?key={KEY}&compress=1"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    resp = r.json()["response"]
    items: dict[str, dict] = {}
    for sku, info in resp.get("items", {}).items():
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

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(PRICE_CACHE, "w") as f:
        json.dump(items, f)
    logger.info("Price cache updated: %s entries", len(items))
    return items


def ensure_currencies_cached():
    if (
        os.path.exists(CURR_CACHE)
        and time.time() - os.path.getmtime(CURR_CACHE) < PRICE_TTL
    ):
        with open(CURR_CACHE) as f:
            data = json.load(f)
        logger.info("Currency cache HIT: %s entries", len(data))
        return data
    logger.info("Fetching currency rates from backpack.tf")
    url = f"https://backpack.tf/api/IGetCurrencies/v1?key={KEY}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()["response"]["currencies"]
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CURR_CACHE, "w") as f:
        json.dump(data, f)
    logger.info("Currency cache updated: %s entries", len(data))
    return data
