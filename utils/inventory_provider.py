from __future__ import annotations

import os
from typing import List

import requests


class InventoryProvider:
    """Fetch TF2 inventories via the Steam Web API."""

    API_URL = "https://api.steampowered.com/IEconItems_440/GetPlayerItems/v0001/"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("STEAM_API_KEY")
        if not self.api_key:
            raise ValueError("STEAM_API_KEY is required")
        self._session = requests.Session()

    def get_inventory(self, steamid: str) -> List[dict]:
        """Return the raw inventory list for ``steamid``."""

        url = f"{self.API_URL}?key={self.api_key}&steamid={steamid}"
        resp = self._session.get(url, timeout=20)
        resp.raise_for_status()
        result = resp.json().get("result", {})
        if result.get("status") != 1:
            raise RuntimeError("Inventory private or unavailable")
        return result.get("items", [])
