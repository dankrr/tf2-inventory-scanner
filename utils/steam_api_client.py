import os
from typing import Any, Dict, Iterator, List, Tuple

import logging
import requests
from dotenv import load_dotenv

# Ensure .env values are available even when this module is imported early.
load_dotenv()

STEAM_API_KEY = os.getenv("STEAM_API_KEY")

logger = logging.getLogger(__name__)


def _require_key() -> str:
    """Return the Steam API key or raise an error if missing."""
    if not STEAM_API_KEY:
        raise RuntimeError(
            "STEAM_API_KEY is required. Set it in the environment or .env file."
        )
    return STEAM_API_KEY


def _chunks(seq: List[str], size: int) -> Iterator[List[str]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def get_player_summaries(steamids: List[str]) -> List[Dict[str, Any]]:
    """Return player summary data for all provided SteamIDs."""
    results: List[Dict[str, Any]] = []
    for chunk in _chunks(steamids, 100):
        key = _require_key()
        url = (
            "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
            f"?key={key}&steamids={','.join(chunk)}"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        players = r.json().get("response", {}).get("players", [])
        results.extend(players)
    return results


def get_inventories(steamids: List[str]) -> Dict[str, Any]:
    """Fetch TF2 inventories for each user via the Steam Web API."""
    results: Dict[str, Any] = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    for chunk in _chunks(steamids, 20):
        for sid in chunk:
            key = _require_key()
            url = (
                "https://api.steampowered.com/IEconItems_440/GetPlayerItems/v0001/"
                f"?key={key}&steamid={sid}"
            )
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            results[sid] = r.json().get("result", {})
    return results


def fetch_inventory(steamid: str) -> Tuple[str, Dict[str, Any]]:
    """Fetch a user's inventory and classify visibility."""

    headers = {"User-Agent": "Mozilla/5.0"}
    key = _require_key()
    url = (
        "https://api.steampowered.com/IEconItems_440/GetPlayerItems/v0001/"
        f"?key={key}&steamid={steamid}"
    )

    try:
        resp = requests.get(url, headers=headers, timeout=20)
    except requests.RequestException:
        logger.info("Inventory %s: Fetch Failed", steamid)
        return "failed", {}

    if resp.status_code in (400, 403):
        logger.info("Inventory %s: Private", steamid)
        return "private", {}

    if resp.status_code != 200:
        logger.info("Inventory %s: HTTP %s", steamid, resp.status_code)
        return "failed", {}

    try:
        data = resp.json()
    except ValueError:
        logger.info("Inventory %s: invalid JSON", steamid)
        return "failed", {}

    result = data.get("result")
    if not isinstance(result, dict):
        logger.info("Inventory %s: Private", steamid)
        return "private", {}
    status_code = result.get("status")
    items = result.get("items") or []

    if status_code == 1:
        if items:
            logger.info(
                "Inventory %s: Public and Parsed (%s items)", steamid, len(items)
            )
            return "parsed", result
        logger.info("Inventory %s: Public but Empty", steamid)
        return "incomplete", result

    logger.info("Inventory %s: Private", steamid)
    return "private", result


def convert_to_steam64(id_str: str) -> str:
    """Convert Steam identifiers to SteamID64.

    The function accepts SteamID64, SteamID2 or SteamID3 strings and
    returns the corresponding SteamID64. Vanity URLs or arbitrary text
    are rejected.
    """

    import re

    if re.fullmatch(r"\d{17}", id_str):
        return id_str

    if re.fullmatch(r"STEAM_0:[01]:\d+", id_str):
        _, y, z = id_str.split(":")
        y = int(y.split("_")[1]) if "_" in y else int(y)
        z = int(z)
        account_id = z * 2 + y
        return str(account_id + 76561197960265728)

    if re.fullmatch(r"\[U:1:\d+\]", id_str):
        z = int(re.search(r"\[U:1:(\d+)\]", id_str).group(1))
        return str(z + 76561197960265728)

    raise ValueError(f"Unsupported SteamID format: {id_str}")


def get_tf2_playtime_hours(steamid: str) -> float:
    """Return TF2 playtime in hours for a Steam user."""
    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    key = _require_key()
    params = {
        "key": key,
        "steamid": steamid,
        "include_played_free_games": 1,
        "format": "json",
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json().get("response", {})
    for game in data.get("games", []):
        if game.get("appid") == 440:
            return game.get("playtime_forever", 0) / 60.0
    return 0.0
