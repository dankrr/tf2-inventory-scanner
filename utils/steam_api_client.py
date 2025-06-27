import os
from typing import List, Dict, Any, Iterator

import requests

STEAM_API_KEY = os.getenv("STEAM_API_KEY")

if not STEAM_API_KEY:
    raise ValueError("STEAM_API_KEY is required")


def _chunks(seq: List[str], size: int) -> Iterator[List[str]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def get_player_summaries(steamids: List[str]) -> List[Dict[str, Any]]:
    """Return player summary data for all provided SteamIDs."""
    results: List[Dict[str, Any]] = []
    for chunk in _chunks(steamids, 100):
        url = (
            "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
            f"?key={STEAM_API_KEY}&steamids={','.join(chunk)}"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        players = r.json().get("response", {}).get("players", [])
        results.extend(players)
    return results


def get_inventories(steamids: List[str]) -> Dict[str, Any]:
    """Fetch TF2 inventories for each user."""
    results: Dict[str, Any] = {}
    for chunk in _chunks(steamids, 20):
        for sid in chunk:
            url = (
                f"https://steamcommunity.com/inventory/{sid}/440/2?l=english&count=5000"
            )
            try:
                r = requests.get(url, timeout=20)
                r.raise_for_status()
                results[sid] = r.json()
            except requests.RequestException:
                results[sid] = {"assets": [], "descriptions": []}
    return results


def convert_to_steam64(id_str: str) -> str:
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

    if id_str.startswith("[U:"):
        match = re.match(r"\[U:(\d+):(\d+)\]", id_str)
        if match:
            z = int(match.group(2))
            return str(z + 76561197960265728)
        match = re.match(r"\[U:1:(\d+)\]", id_str)
        if match:
            z = int(match.group(1))
            return str(z + 76561197960265728)

    url = (
        "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
        f"?key={STEAM_API_KEY}&vanityurl={id_str}"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json().get("response", {})
    if data.get("success") != 1:
        raise ValueError(f"Unable to resolve vanity URL: {id_str}")
    return data["steamid"]


def get_tf2_playtime_hours(steamid: str) -> float:
    """Return TF2 playtime in hours for a Steam user."""
    url = (
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
        f"?key={STEAM_API_KEY}&steamid={steamid}&appids_filter[0]=440"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json().get("response", {})
    for game in data.get("games", []):
        if game.get("appid") == 440:
            return game.get("playtime_forever", 0) / 60.0
    return 0.0
