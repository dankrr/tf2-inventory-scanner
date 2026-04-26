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
VANITY_RE = re.compile(r"^[A-Za-z0-9_-]{2,32}$")
VANITY_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?steamcommunity\.com/id/([A-Za-z0-9_-]{2,32})/?",
    re.IGNORECASE,
)


def extract_steam_ids(raw_text: str) -> List[str]:
    """Return unique Steam ID tokens found in ``raw_text``.

    Supports SteamID64/2/3 tokens and vanity URLs in ``steamcommunity.com/id``
    form while avoiding accidental username matches from TF2 ``status`` dumps.
    """

    ids: List[str] = []
    seen: set[str] = set()
    text = raw_text.strip()
    tokens = re.split(r"\s+", text) if text else []

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
    for match in VANITY_URL_RE.finditer(text):
        vanity = match.group(1)
        if vanity not in seen:
            seen.add(vanity)
            ids.append(vanity)

    return ids


async def resolve_vanity_url_async(vanity: str) -> str | None:
    """Resolve a Steam vanity string to SteamID64, or ``None`` on failure."""

    key = _require_key()
    url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, params={"key": key, "vanityurl": vanity})
        except httpx.HTTPError:
            logger.warning("Vanity resolve failed for %s", vanity)
            return None
    if resp.status_code != 200:
        return None
    try:
        payload = resp.json().get("response", {})
    except ValueError:
        return None
    if payload.get("success") == 1 and payload.get("steamid"):
        return str(payload.get("steamid"))
    return None


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
    """Convert Steam identifiers (SteamID64, SteamID2, SteamID3, vanity) to SteamID64."""

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

    if VANITY_RE.fullmatch(id_str):
        key = _require_key()
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(
                    "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/",
                    params={"key": key, "vanityurl": id_str},
                )
        except httpx.HTTPError:
            logger.warning("Vanity resolve failed for %s", id_str)
            raise ValueError(f"Invalid Steam ID format: {id_str}")
        if resp.status_code != 200:
            logger.warning(
                "Vanity resolve HTTP %s for %s", resp.status_code, id_str
            )
            raise ValueError(f"Invalid Steam ID format: {id_str}")
        try:
            payload = resp.json().get("response", {})
        except ValueError:
            logger.warning("Vanity resolve returned invalid JSON for %s", id_str)
            raise ValueError(f"Invalid Steam ID format: {id_str}")
        if payload.get("success") == 1 and payload.get("steamid"):
            return str(payload.get("steamid"))

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
