import os
from typing import Any, Dict, Iterator, List, Tuple

import logging
import httpx
import re
from dotenv import load_dotenv

# Ensure .env values are available even when this module is imported early.
load_dotenv()

STEAM_API_KEY = os.getenv("STEAM_API_KEY")

logger = logging.getLogger(__name__)


def _require_key() -> str:
    """Return the Steam API key or raise an error if missing."""
    if not STEAM_API_KEY:
        raise ValueError(
            "STEAM_API_KEY is required. Set it in the environment or .env file."
        )
    return STEAM_API_KEY


def _chunks(seq: List[str], size: int) -> Iterator[List[str]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


# ---------------------------------------------------------------------------
# Steam ID parsing helpers

STEAMID2_RE = re.compile(r"^STEAM_0:[01]:\d+$")
STEAMID3_RE = re.compile(r"^\[U:1:\d+\]$")
STEAMID64_RE = re.compile(r"^\d{17}$")


def extract_steam_ids(raw_text: str) -> List[str]:
    """Return unique Steam ID tokens found in ``raw_text``."""

    tokens = re.split(r"\s+", raw_text.strip())
    ids: List[str] = []
    seen: set[str] = set()

    for token in tokens:
        if not token:
            continue
        if (
            STEAMID2_RE.fullmatch(token)
            or STEAMID3_RE.fullmatch(token)
            or STEAMID64_RE.fullmatch(token)
        ):
            if token not in seen:
                seen.add(token)
                ids.append(token)
    return ids


async def get_player_summaries_async(steamids: List[str]) -> List[Dict[str, Any]]:
    """Asynchronously return player summary data for the provided SteamIDs."""
    results: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=10) as client:
        for chunk in _chunks(steamids, 100):
            key = _require_key()
            url = (
                "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
                f"?key={key}&steamids={','.join(chunk)}"
            )
            try:
                resp = await client.get(url)
            except httpx.HTTPError:
                logger.warning("Player summaries fetch failed for %s", chunk)
                continue
            if resp.status_code in (420, 429):
                logger.warning("Player summaries rate limited for %s", chunk)
                continue
            if resp.status_code != 200:
                logger.warning(
                    "Player summaries HTTP %s for %s", resp.status_code, chunk
                )
                continue
            try:
                players = resp.json().get("response", {}).get("players", [])
            except ValueError:
                players = []
            results.extend(players)
    return results


async def fetch_inventory_async(steamid: str) -> Tuple[str, Dict[str, Any]]:
    """Asynchronously fetch and classify a user's TF2 inventory."""

    headers = {"User-Agent": "Mozilla/5.0"}
    key = _require_key()
    url = (
        "https://api.steampowered.com/IEconItems_440/GetPlayerItems/v0001/"
        f"?key={key}&steamid={steamid}"
    )

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(url, headers=headers)
        except httpx.HTTPError:
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
    """Convert Steam identifiers (SteamID64, SteamID2, SteamID3) to SteamID64."""

    if re.fullmatch(r"\d{17}", id_str):
        return id_str

    match = re.fullmatch(r"STEAM_0:([01]):(\d+)", id_str)
    if match:
        y = int(match.group(1))
        z = int(match.group(2))
        account_id = z * 2 + y
        return str(account_id + 76561197960265728)

    match = re.fullmatch(r"\[U:1:(\d+)\]", id_str)
    if match:
        z = int(match.group(1))
        return str(z + 76561197960265728)

    raise ValueError(f"Invalid Steam ID format: {id_str}")


async def get_tf2_playtime_hours_async(steamid: str) -> float:
    """Asynchronously return TF2 playtime in hours for a Steam user."""
    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    key = _require_key()
    params = {
        "key": key,
        "steamid": steamid,
        "include_played_free_games": 1,
        "format": "json",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, params=params)
        except httpx.HTTPError:
            logger.warning("Playtime fetch failed for %s", steamid)
            return 0.0
    if resp.status_code in (420, 429):
        logger.warning("Playtime rate limited for %s", steamid)
        return 0.0
    if resp.status_code != 200:
        logger.warning("Playtime HTTP %s for %s", resp.status_code, steamid)
        return 0.0
    try:
        data = resp.json().get("response", {})
    except ValueError:
        return 0.0
    for game in data.get("games", []):
        if game.get("appid") == 440:
            return game.get("playtime_forever", 0) / 60.0
    return 0.0
