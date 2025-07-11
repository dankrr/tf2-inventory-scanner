from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from .constants import KILLSTREAK_TIERS

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

PRICES_FILE = Path("cache/prices.json")
CURRENCIES_FILE = Path("cache/currencies.json")
PRICE_MAP_FILE = Path("cache/price_map.json")


def _key_to_str(key: tuple[str, int, bool, int, int]) -> str:
    """Return serialized price map key for JSON storage."""

    name, quality, australium, effect, ks = key
    return f"{name}|{quality}|{1 if australium else 0}|{effect}|{ks}"


def _str_to_key(key: str) -> tuple[str, int, bool, int, int]:
    """Return tuple key from serialized form."""

    name, quality, australium, effect, ks = key.split("|", 4)
    return (
        name,
        int(quality),
        bool(int(australium)),
        int(effect),
        int(ks),
    )


QUALITY_PREFIXES = (
    "Strange ",
    "Genuine ",
    "Vintage ",
    "Collector's ",
    "Haunted ",
    "Unusual ",
    "Decorated ",
    "Civilian Grade ",
    "Freelance Grade ",
    "Mercenary Grade ",
    "Commando Grade ",
    "Assassin Grade ",
    "Elite Grade ",
)


def _strip_quality(name: str) -> str:
    for q in QUALITY_PREFIXES:
        if name.startswith(q):
            return name[len(q) :]
    return name


def _extract_killstreak(name: str) -> tuple[str, int]:
    """Return (base name, killstreak tier) from an item name."""

    name_no_qual = _strip_quality(name)

    for tier in (3, 2, 1):
        prefix = f"{KILLSTREAK_TIERS[tier]} "
        if name_no_qual.startswith(prefix):
            base = name_no_qual[len(prefix) :]
            return base, tier
    return name_no_qual, 0


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


def build_price_map(
    prices_path: Path,
) -> dict[tuple[str, int, bool, int, int], dict]:
    """Return mapping of ``(item_name, quality, is_australium, effect_id, killstreak_tier)`` -> price info."""

    with prices_path.open() as f:
        data = json.load(f)

    items = data.get("response", {}).get("items", {})
    mapping: dict[tuple[str, int, bool, int, int], dict] = {}

    for name, item in items.items():
        is_australium = str(item.get("australium")) == "1" or name.startswith(
            "Australium "
        )
        base_name = (
            name.replace("Australium ", "") if name.startswith("Australium ") else name
        )
        base_name, ks_tier = _extract_killstreak(base_name)
        prices = item.get("prices", {})
        for quality, qdata in prices.items():
            try:
                qid = int(quality)
            except (TypeError, ValueError):
                continue

            tradable = qdata.get("Tradable", {})
            entries = tradable.get("Craftable")

            if qid == 5 and isinstance(entries, dict):
                effect_entries = entries
            else:
                if not isinstance(entries, list):
                    entries = tradable.get("Non-Craftable")
                entry = entries[0] if isinstance(entries, list) else None
                effect_entries = {0: entry} if isinstance(entry, dict) else {}

            for effect_key, entry in effect_entries.items():
                if not isinstance(entry, dict):
                    continue

                value_raw = entry.get("value_raw")
                currency = entry.get("currency")
                if value_raw is None or currency is None:
                    continue

                try:
                    effect_id = int(effect_key)
                except (TypeError, ValueError):
                    effect_id = 0

                mapping[(base_name, qid, is_australium, effect_id, ks_tier)] = {
                    "value_raw": float(value_raw),
                    "currency": str(currency),
                }
    return mapping


def ensure_price_map_cached(refresh: bool = False) -> Path:
    """Return path to cached price map JSON, building if needed."""

    if PRICE_MAP_FILE.exists() and not refresh:
        if not PRICES_FILE.exists():
            return PRICE_MAP_FILE
        try:
            if PRICE_MAP_FILE.stat().st_mtime >= PRICES_FILE.stat().st_mtime:
                return PRICE_MAP_FILE
        except OSError:
            pass

    prices_path = ensure_prices_cached(refresh=refresh)
    price_map = build_price_map(prices_path)
    data = {_key_to_str(k): v for k, v in price_map.items()}
    PRICE_MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    PRICE_MAP_FILE.write_text(json.dumps(data, indent=2))
    try:
        PRICES_FILE.unlink()
    except FileNotFoundError:
        pass
    return PRICE_MAP_FILE


def load_price_map(path: Path) -> dict[tuple[str, int, bool, int, int], dict]:
    """Return price map dictionary from ``path``."""

    with path.open() as f:
        data = json.load(f)
    mapping: dict[tuple[str, int, bool, int, int], dict] = {}
    for key, value in data.items():
        try:
            mapping[_str_to_key(key)] = value
        except Exception:
            continue
    return mapping
