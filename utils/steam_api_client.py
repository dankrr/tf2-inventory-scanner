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
