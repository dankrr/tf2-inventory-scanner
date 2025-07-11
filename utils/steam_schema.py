from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

import httpx

from .steam_api_client import _require_key


class SteamSchemaProvider:
    """Fetch and cache TF2 schema data from the official Steam Web API."""

    TTL = 24 * 60 * 60  # 24 hours
    OVERVIEW_URL = (
        "https://api.steampowered.com/IEconItems_440/GetSchemaOverview/v0001/"
    )
    ITEMS_URL = "https://api.steampowered.com/IEconItems_440/GetSchemaItems/v0001/"

    def __init__(self, cache_file: str | Path = "data/schema_steam.json") -> None:
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._schema: Dict[str, Any] | None = None

    async def load_schema(
        self, *, force: bool = False, language: str = "en"
    ) -> Dict[str, Any]:
        """Return the cached schema dictionary, refreshing if needed."""

        if self._schema is None or force:
            self._schema = await self._load(force=force, language=language)
        return self._schema

    async def _load(self, *, force: bool, language: str) -> Dict[str, Any]:
        if not force and self.cache_file.exists():
            age = time.time() - self.cache_file.stat().st_mtime
            if age < self.TTL:
                with self.cache_file.open() as f:
                    return json.load(f)

        data = await self._fetch(language=language)
        self.cache_file.write_text(json.dumps(data, indent=2))
        return data

    async def _fetch(self, *, language: str) -> Dict[str, Any]:
        key = _require_key()
        params = {"key": key, "language": language, "format": "json"}
        async with httpx.AsyncClient(timeout=20) as client:
            overview_resp = await client.get(self.OVERVIEW_URL, params=params)
            overview_resp.raise_for_status()
            overview = overview_resp.json().get("result", {})

            items: list[dict] = []
            start = 0
            while True:
                item_params = params.copy()
                if start:
                    item_params["start"] = start
                items_resp = await client.get(self.ITEMS_URL, params=item_params)
                items_resp.raise_for_status()
                payload = items_resp.json().get("result", {})
                items.extend(payload.get("items", []))
                if payload.get("next") is None:
                    break
                start = payload["next"]

        attributes = overview.get("attributes", [])
        particles = overview.get("attribute_controlled_attached_particles", [])
        qualities = overview.get("qualities", {})
        origins = overview.get("originNames", [])

        items_by_defindex = {
            int(item["defindex"]): item
            for item in items
            if isinstance(item, dict) and "defindex" in item
        }
        attributes_by_defindex = {
            int(attr["defindex"]): attr
            for attr in attributes
            if isinstance(attr, dict) and "defindex" in attr
        }
        particles_by_index = {
            int(p["id"]): p.get("name", "")
            for p in particles
            if isinstance(p, dict) and "id" in p
        }
        qualities_by_index: Dict[int, str] = {}
        if isinstance(qualities, dict):
            for k, v in qualities.items():
                if str(k).isdigit():
                    qualities_by_index[int(k)] = str(v)
                elif str(v).isdigit():
                    qualities_by_index[int(v)] = str(k)
        origins_by_index = {
            int(o.get("origin", o.get("id"))): str(o.get("name"))
            for o in origins
            if isinstance(o, dict)
            and ("origin" in o or "id" in o)
            and (o.get("origin") or o.get("id")) is not None
        }

        return {
            "items_by_defindex": items_by_defindex,
            "qualities_by_index": qualities_by_index,
            "attributes_by_defindex": attributes_by_defindex,
            "particles_by_index": particles_by_index,
            "origins_by_index": origins_by_index,
        }
