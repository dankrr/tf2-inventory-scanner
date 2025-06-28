import os
import json
import time
import logging
import requests

PRICE_TTL = 900
CACHE_DIR = "data"
PRICE_CACHE = f"{CACHE_DIR}/price_schema.json"
CURR_CACHE = f"{CACHE_DIR}/currencies.json"
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
        logger.info("Price cache HIT: %s entries", len(data.get("items", {})))
        return data
    logger.info("Fetching prices from backpack.tf")
    r = requests.get(f"https://backpack.tf/api/IGetPrices/v4?raw=2&key={KEY}")
    r.raise_for_status()
    data = r.json()["response"]
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(PRICE_CACHE, "w") as f:
        json.dump(data, f)
    logger.info("Price cache updated: %s entries", len(data.get("items", {})))
    return data


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
    r = requests.get(f"https://backpack.tf/api/IGetCurrencies/v1?key={KEY}")
    r.raise_for_status()
    data = r.json()["response"]["currencies"]
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CURR_CACHE, "w") as f:
        json.dump(data, f)
    logger.info("Currency cache updated: %s entries", len(data))
    return data
