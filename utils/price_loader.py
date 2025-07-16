from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import time
import asyncio

from .constants import KILLSTREAK_TIERS

import httpx
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

PRICES_FILE = Path("cache/prices.json")
CURRENCIES_FILE = Path("cache/currencies.json")
PRICE_MAP_FILE = Path("cache/price_map.json")

# ANSI color codes
COLOR_YELLOW = "\033[33m"
COLOR_RESET = "\033[0m"

# bytes
EMPTY_THRESHOLD = 512 * 1024


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
    if path.exists():
        size = path.stat().st_size
        if size < EMPTY_THRESHOLD:
            print(
                f"{COLOR_YELLOW}⚠ Detected incomplete price cache ({size} bytes). Deleting and retrying...{COLOR_RESET}"
            )
            try:
                path.unlink()
            finally:
                refresh = True
    if path.exists() and not refresh:
        return path

    url = f"https://backpack.tf/api/IGetPrices/v4?raw=1&key={_require_key()}"
    retries = int(os.getenv("PRICE_RETRIES", "3"))
    delay = int(os.getenv("PRICE_DELAY", "5"))
    last_err: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=5, headers={"accept": "application/json"})
            resp.raise_for_status()
            data = resp.json()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2))
            return path
        except Exception as exc:  # requests or JSON
            last_err = exc
            logger.warning("Failed to fetch prices: %s", exc)
            if attempt < retries:
                time.sleep(delay)

    warn = (
        f"{COLOR_YELLOW}⚠ Could not fetch Backpack.tf prices after {retries} attempts (last error: {last_err}).\n"
        f"Pricing features disabled. Run with --refresh when online to restore.{COLOR_RESET}"
    )
    print(warn)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
    return path


async def ensure_prices_cached_async(refresh: bool = False) -> Path:
    """Async version of :func:`ensure_prices_cached`."""

    path = PRICES_FILE
    if path.exists():
        size = path.stat().st_size
        if size < EMPTY_THRESHOLD:
            print(
                f"{COLOR_YELLOW}⚠ Detected incomplete price cache ({size} bytes). Deleting and retrying...{COLOR_RESET}"
            )
            try:
                path.unlink()
            finally:
                refresh = True
    if path.exists() and not refresh:
        return path

    url = f"https://backpack.tf/api/IGetPrices/v4?raw=1&key={_require_key()}"
    retries = int(os.getenv("PRICE_RETRIES", "3"))
    delay = int(os.getenv("PRICE_DELAY", "5"))
    last_err: Exception | None = None

    async with httpx.AsyncClient() as client:
        for attempt in range(1, retries + 1):
            try:
                resp = await client.get(
                    url, timeout=5, headers={"accept": "application/json"}
                )
                resp.raise_for_status()
                data = resp.json()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(data, indent=2))
                return path
            except Exception as exc:  # httpx or JSON
                last_err = exc
                logger.warning("Failed to fetch prices: %s", exc)
                if attempt < retries:
                    await asyncio.sleep(delay)

    warn = (
        f"{COLOR_YELLOW}⚠ Could not fetch Backpack.tf prices after {retries} attempts (last error: {last_err}).\n"
        f"Pricing features disabled. Run with --refresh when online to restore.{COLOR_RESET}"
    )
    print(warn)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
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


async def ensure_currencies_cached_async(refresh: bool = False) -> Path:
    """Async version of :func:`ensure_currencies_cached`."""

    path = CURRENCIES_FILE
    if path.exists() and not refresh:
        return path

    url = f"https://backpack.tf/api/IGetCurrencies/v1?raw=1&key={_require_key()}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                url, timeout=5, headers={"accept": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # httpx or JSON
            logger.warning("Failed to fetch currencies: %s", exc)
            if path.exists():
                return path
            raise RuntimeError("Cannot fetch Backpack.tf currencies") from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    return path


def build_price_map(
    prices_path: Path,
) -> dict[tuple[str, int, bool, bool, int, int], dict]:
    """Return mapping of ``(item_name, quality, craftable, is_australium, effect_id, killstreak_tier)`` -> price info."""

    with prices_path.open() as f:
        data = json.load(f)

    items = data.get("response", {}).get("items", {})
    mapping: dict[tuple[str, int, bool, bool, int, int], dict] = {}

    for name, item in items.items():
        is_australium = str(item.get("australium")) == "1" or name.startswith(
            "Australium "
        )
        base_name = (
            name.replace("Australium ", "") if name.startswith("Australium ") else name
        )
        base_name = base_name.replace("\n", " ")
        base_name, ks_tier = _extract_killstreak(base_name)
        prices = item.get("prices", {})
        for quality, qdata in prices.items():
            try:
                qid = int(quality)
            except (TypeError, ValueError):
                continue

            tradable = qdata.get("Tradable", {})
            for craft_key in ("Craftable", "Non-Craftable"):
                craftable = craft_key == "Craftable"
                entries = tradable.get(craft_key)

                if isinstance(entries, dict):
                    effect_entries = entries
                else:
                    entry = entries[0] if isinstance(entries, list) else None
                    effect_entries = {0: entry} if isinstance(entry, dict) else {}

                is_crate_case = (
                    "crate" in base_name.lower() or "case" in base_name.lower()
                )
                for effect_key, entry in effect_entries.items():
                    if not isinstance(entry, dict):
                        continue

                    value_raw = entry.get("value_raw", entry.get("value"))
                    currency = entry.get("currency")
                    if value_raw is None or currency is None:
                        continue

                    try:
                        effect_id = int(effect_key)
                    except (TypeError, ValueError):
                        effect_id = 0

                    info = {
                        "value_raw": float(value_raw),
                        "currency": str(currency),
                    }
                    mapping[
                        (base_name, qid, craftable, is_australium, effect_id, ks_tier)
                    ] = info
                    if is_crate_case and effect_id != 0:
                        mapping[
                            (base_name, qid, craftable, is_australium, 0, ks_tier)
                        ] = info
    return mapping


def dump_price_map(
    price_map: dict[tuple[str, int, bool, bool, int, int], dict],
    path: Path = PRICE_MAP_FILE,
) -> Path:
    """Serialize ``price_map`` to ``path``."""

    data = [[list(key), value] for key, value in price_map.items()]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return path


def load_price_map(
    path: Path = PRICE_MAP_FILE,
) -> dict[tuple[str, int, bool, bool, int, int], dict]:
    """Load mapping previously saved by :func:`dump_price_map`."""

    with path.open() as f:
        data = json.load(f)

    mapping: dict[tuple[str, int, bool, bool, int, int], dict] = {}
    if isinstance(data, list):
        for key, value in data:
            if not isinstance(key, list) or len(key) != 6:
                continue
            mapping[
                (
                    str(key[0]),
                    int(key[1]),
                    bool(key[2]),
                    bool(key[3]),
                    int(key[4]),
                    int(key[5]),
                )
            ] = value
    return mapping
