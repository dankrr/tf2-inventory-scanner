import os
import logging
from typing import Any, Dict, Iterator, List, Tuple

import aiohttp
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


async def get_player_summaries(steamids: List[str]) -> List[Dict[str, Any]]:
    """Return player summary data for all provided SteamIDs."""

    results: List[Dict[str, Any]] = []
    async with aiohttp.ClientSession() as session:
        for chunk in _chunks(steamids, 100):
            key = _require_key()
            url = (
                "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
                f"?key={key}&steamids={','.join(chunk)}"
            )
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                players = data.get("response", {}).get("players", [])
                results.extend(players)
    return results


async def get_inventories(steamids: List[str]) -> Dict[str, Any]:
    """Fetch TF2 inventories for each user via the Steam Web API."""

    results: Dict[str, Any] = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession() as session:
        for chunk in _chunks(steamids, 20):
            for sid in chunk:
                key = _require_key()
                url = (
                    "https://api.steampowered.com/IEconItems_440/GetPlayerItems/v0001/"
                    f"?key={key}&steamid={sid}"
                )
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    results[sid] = data.get("result", {})
    return results


async def fetch_inventory(steamid: str) -> Tuple[str, Dict[str, Any]]:
    """Fetch a user's inventory and classify visibility."""

    headers = {"User-Agent": "Mozilla/5.0"}
    key = _require_key()
    url = (
        "https://api.steampowered.com/IEconItems_440/GetPlayerItems/v0001/"
        f"?key={key}&steamid={steamid}"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status in (400, 403):
                    logger.info("Inventory %s: Private", steamid)
                    return "private", {}
                if resp.status != 200:
                    logger.info("Inventory %s: HTTP %s", steamid, resp.status)
                    return "failed", {}
                try:
                    data = await resp.json()
                except ValueError:
                    logger.info("Inventory %s: invalid JSON", steamid)
                    return "failed", {}
    except aiohttp.ClientError:
        logger.info("Inventory %s: Fetch Failed", steamid)
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


async def convert_to_steam64(id_str: str) -> str:
    """Convert Steam identifiers to SteamID64."""
    import re

    if re.fullmatch(r"\d{17}", id_str):
        return id_str

    if id_str.startswith("STEAM_"):
        try:
            _, y, z = id_str.split(":")
            y = int(y.split("_")[1]) if "_" in y else int(y)
            z = int(z)
        except (ValueError, IndexError):
            raise ValueError(f"Invalid SteamID2: {id_str}") from None
        account_id = z * 2 + y
        return str(account_id + 76561197960265728)

    if id_str.upper().startswith("[U:"):
        match = re.match(r"\[U:(\d+):(\d+)\]", id_str, re.IGNORECASE)
        if match:
            z = int(match.group(2))
            return str(z + 76561197960265728)
        match = re.match(r"\[U:1:(\d+)\]", id_str, re.IGNORECASE)
        if match:
            z = int(match.group(1))
            return str(z + 76561197960265728)

    key = _require_key()
    url = (
        "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
        f"?key={key}&vanityurl={id_str}"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            data = await resp.json()
    data = data.get("response", {})
    if data.get("success") != 1:
        raise ValueError(f"Unable to resolve vanity URL: {id_str}")
    return data["steamid"]


async def get_tf2_playtime_hours(steamid: str) -> float:
    """Return TF2 playtime in hours for a Steam user."""

    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    key = _require_key()
    params = {
        "key": key,
        "steamid": steamid,
        "include_played_free_games": 1,
        "format": "json",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            params=params,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

    data = data.get("response", {})
    for game in data.get("games", []):
        if game.get("appid") == 440:
            return game.get("playtime_forever", 0) / 60.0
    return 0.0
