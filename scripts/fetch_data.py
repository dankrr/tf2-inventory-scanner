import json
import os
from pathlib import Path
from typing import Any

import requests

SCHEMA_ITEMS_URL = (
    "https://api.steampowered.com/IEconItems_440/GetSchemaItems/v1/"
    "?key={key}&format=json"
)
SCHEMA_OVERVIEW_URL = (
    "https://api.steampowered.com/IEconItems_440/GetSchemaOverview/v1/"
    "?key={key}&format=json"
)
ITEMS_GAME_URL = (
    "https://raw.githubusercontent.com/SteamDatabase/SteamTracking/master/"
    "TeamFortress2/tf/scripts/items/items_game.txt"
)
INVENTORY_URL = (
    "https://steamcommunity.com/inventory/{steamid}/440/2?l=english&count=5000"
)

CACHE_DIR = Path("cache")


def _download(url: str) -> Any:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    if url.endswith(".txt"):
        return resp.text
    return resp.json()


def fetch_schema_items(api_key: str, dest: Path | None = None) -> Path:
    if dest is None:
        dest = CACHE_DIR / "schema_items.json"
    data = _download(SCHEMA_ITEMS_URL.format(key=api_key))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data))
    return dest


def fetch_schema_overview(api_key: str, dest: Path | None = None) -> Path:
    if dest is None:
        dest = CACHE_DIR / "schema_overview.json"
    data = _download(SCHEMA_OVERVIEW_URL.format(key=api_key))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data))
    return dest


def fetch_items_game(dest: Path | None = None) -> Path:
    if dest is None:
        dest = CACHE_DIR / "items_game.txt"
    text = _download(ITEMS_GAME_URL)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)
    return dest


def fetch_inventory(steamid: str, dest: Path | None = None) -> Path:
    if dest is None:
        dest = CACHE_DIR / f"inventory_{steamid}.json"
    data = _download(INVENTORY_URL.format(steamid=steamid))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data))
    return dest


def fetch_all(api_key: str | None = None, steamid: str | None = None) -> None:
    api_key = api_key or os.getenv("STEAM_API_KEY")
    steamid = steamid or os.getenv("TEST_STEAM_ID")
    if not api_key or not steamid:
        raise ValueError("STEAM_API_KEY and TEST_STEAM_ID are required")

    fetch_schema_items(api_key)
    fetch_schema_overview(api_key)
    fetch_items_game()
    fetch_inventory(steamid)


if __name__ == "__main__":
    fetch_all()
