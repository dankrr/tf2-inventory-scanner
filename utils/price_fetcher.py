import os
import json
import time
import requests

PRICE_TTL = 900
CACHE_DIR = "data"
PRICE_CACHE = f"{CACHE_DIR}/price_schema.json"
CURR_CACHE = f"{CACHE_DIR}/currencies.json"
KEY = os.getenv("BACKPACK_KEY")


def ensure_prices_cached():
    if (
        os.path.exists(PRICE_CACHE)
        and time.time() - os.path.getmtime(PRICE_CACHE) < PRICE_TTL
    ):
        with open(PRICE_CACHE) as f:
            return json.load(f)
    r = requests.get(f"https://backpack.tf/api/IGetPrices/v4?raw=2&key={KEY}")
    r.raise_for_status()
    data = r.json()["response"]
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(PRICE_CACHE, "w") as f:
        json.dump(data, f)
    return data


def ensure_currencies_cached():
    if (
        os.path.exists(CURR_CACHE)
        and time.time() - os.path.getmtime(CURR_CACHE) < PRICE_TTL
    ):
        with open(CURR_CACHE) as f:
            return json.load(f)
    r = requests.get(f"https://backpack.tf/api/IGetCurrencies/v1?key={KEY}")
    r.raise_for_status()
    data = r.json()["response"]["currencies"]
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CURR_CACHE, "w") as f:
        json.dump(data, f)
    return data
