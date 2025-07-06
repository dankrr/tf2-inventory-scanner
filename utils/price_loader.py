from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

PRICES_FILE = Path("cache/prices.json")
CURRENCIES_FILE = Path("cache/currencies.json")


def _require_key() -> str:
    key = os.getenv("BPTF_API_KEY")
    if not key:
        raise RuntimeError(
            "BPTF_API_KEY is required. Set it in the environment or .env file."
        )
    return key


def ensure_prices_cached(refresh: bool = False) -> Path:
    """Download price dump from backpack.tf if needed and return cache path."""

    path = PRICES_FILE
    if path.exists() and not refresh:
        return path

    url = f"https://backpack.tf/api/IGetPrices/v4?raw=1&key={_require_key()}"
    try:
        resp = requests.get(url, timeout=5, headers={"accept": "application/json"})
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # requests or JSON
        logger.warning("Failed to fetch prices: %s", exc)
        if path.exists():
            return path
        raise RuntimeError("Cannot fetch Backpack.tf prices") from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    return path


def ensure_currencies_cached(refresh: bool = False) -> Path:
    """Download currency exchange rates from backpack.tf."""

    path = CURRENCIES_FILE
    if path.exists() and not refresh:
        return path

    url = f"https://backpack.tf/api/IGetCurrencies/v1?raw=1&key={_require_key()}"
    try:
        resp = requests.get(url, timeout=5, headers={"accept": "application/json"})
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # requests or JSON
        logger.warning("Failed to fetch currencies: %s", exc)
        if path.exists():
            return path
        raise RuntimeError("Cannot fetch Backpack.tf currencies") from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    return path


def build_price_map(prices_path: Path) -> dict[tuple[int, int], dict]:
    """Return mapping of (defindex, quality) -> price info."""

    with prices_path.open() as f:
        data = json.load(f)

    items = data.get("response", {}).get("items", {})
    mapping: dict[tuple[int, int], dict] = {}

    for item in items.values():
        defindexes = item.get("defindex") or []
        prices = item.get("prices", {})
        for quality, qdata in prices.items():
            try:
                qid = int(quality)
            except (TypeError, ValueError):
                continue

            tradable = qdata.get("Tradable", {})
            entries = tradable.get("Craftable")
            if not isinstance(entries, list):
                entries = tradable.get("Non-Craftable")

            entry = entries[0] if isinstance(entries, list) else None
            if not isinstance(entry, dict):
                continue
            value_raw = entry.get("value_raw")
            currency = entry.get("currency")
            if value_raw is None or currency is None:
                continue
            for defi in defindexes:
                try:
                    idx = int(defi)
                except (TypeError, ValueError):
                    continue
                mapping[(idx, qid)] = {
                    "value_raw": float(value_raw),
                    "currency": str(currency),
                }
    return mapping
