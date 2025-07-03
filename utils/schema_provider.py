from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

import requests


class SchemaProvider:
    """Fetch and cache TF2 schema data from schema.autobot.tf."""

    TTL = 48 * 60 * 60  # 48 hours
    ENDPOINTS = {
        "items": "/items",
        "attributes": "/attributes",
        "effects": "/effects",
        "paints": "/paints",
        "origins": "/origins",
        "parts": "/parts",
        "qualities": "/qualities",
    }

    def __init__(
        self,
        base_url: str = "https://schema.autobot.tf",
        cache_dir: str | Path = "cache/schema",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._session = requests.Session()
        self.items_by_defindex: Dict[int, Any] | None = None
        self.attributes_by_defindex: Dict[int, Any] | None = None
        self.effects_by_index: Dict[int, str] | None = None
        self.paints_by_defindex: Dict[int, str] | None = None
        self.origins_by_index: Dict[int, str] | None = None
        self.parts_by_defindex: Dict[int, str] | None = None
        self.qualities_by_index: Dict[int, str] | None = None

    # ------------------------------------------------------------------
    def _fetch(self, endpoint: str) -> Any:
        url = f"{self.base_url}{endpoint}"
        resp = self._session.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def _cache_file(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def _load(self, key: str, endpoint: str, force: bool = False) -> Any:
        path = self._cache_file(key)
        data: Any | None = None
        if not force and path.exists():
            age = time.time() - path.stat().st_mtime
            if age < self.TTL:
                with path.open() as f:
                    data = json.load(f)
        if data is None:
            data = self._fetch(endpoint)
            path.write_text(json.dumps(data))
        return data

    # ------------------------------------------------------------------
    def refresh_all(self) -> None:
        """Force refresh of all schema files."""
        for key, ep in self.ENDPOINTS.items():
            self._load(key, ep, force=True)
            setattr(
                self,
                (
                    f"{key}_by_defindex"
                    if key in {"items", "attributes", "paints", "parts"}
                    else f"{key}_by_index"
                ),
                None,
            )

    def _to_int_map(self, data: dict) -> Dict[int, Any]:
        mapping: Dict[int, Any] = {}
        for k, v in data.items():
            if str(k).isdigit():
                mapping[int(k)] = v
            elif str(v).isdigit():
                mapping[int(v)] = k
        return mapping

    # ------------------------------------------------------------------
    def get_items(self, *, force: bool = False) -> Dict[int, Any]:
        if self.items_by_defindex is None or force:
            data = self._load("items", self.ENDPOINTS["items"], force)
            self.items_by_defindex = (
                self._to_int_map(data) if isinstance(data, dict) else {}
            )
        return self.items_by_defindex

    def get_attributes(self, *, force: bool = False) -> Dict[int, Any]:
        if self.attributes_by_defindex is None or force:
            data = self._load("attributes", self.ENDPOINTS["attributes"], force)
            self.attributes_by_defindex = (
                self._to_int_map(data) if isinstance(data, dict) else {}
            )
        return self.attributes_by_defindex

    def _from_name_map(self, data: dict) -> Dict[int, str]:
        mapping: Dict[int, str] = {}
        for k, v in data.items():
            if str(k).isdigit():
                mapping[int(k)] = str(v)
            elif str(v).isdigit():
                mapping[int(v)] = str(k)
        return mapping

    def get_effects(self, *, force: bool = False) -> Dict[int, str]:
        if self.effects_by_index is None or force:
            data = self._load("effects", self.ENDPOINTS["effects"], force)
            self.effects_by_index = (
                self._from_name_map(data) if isinstance(data, dict) else {}
            )
        return self.effects_by_index

    def get_paints(self, *, force: bool = False) -> Dict[int, str]:
        if self.paints_by_defindex is None or force:
            data = self._load("paints", self.ENDPOINTS["paints"], force)
            self.paints_by_defindex = (
                self._from_name_map(data) if isinstance(data, dict) else {}
            )
        return self.paints_by_defindex

    def get_origins(self, *, force: bool = False) -> Dict[int, str]:
        if self.origins_by_index is None or force:
            data = self._load("origins", self.ENDPOINTS["origins"], force)
            self.origins_by_index = (
                self._from_name_map(data) if isinstance(data, dict) else {}
            )
        return self.origins_by_index

    def get_parts(self, *, force: bool = False) -> Dict[int, str]:
        if self.parts_by_defindex is None or force:
            data = self._load("parts", self.ENDPOINTS["parts"], force)
            self.parts_by_defindex = (
                self._from_name_map(data) if isinstance(data, dict) else {}
            )
        return self.parts_by_defindex

    def get_qualities(self, *, force: bool = False) -> Dict[int, str]:
        if self.qualities_by_index is None or force:
            data = self._load("qualities", self.ENDPOINTS["qualities"], force)
            self.qualities_by_index = (
                self._from_name_map(data) if isinstance(data, dict) else {}
            )
        return self.qualities_by_index

    # Compatibility helpers -------------------------------------------------
    def get_defindexes(self, *, force: bool = False) -> Dict[int, Any]:
        return self.get_items(force=force)

    def get_strangeParts(self, *, force: bool = False) -> Dict[int, str]:
        return self.get_parts(force=force)

    # Stub helpers kept for backward compatibility --------------------------
    def get_paintkits(self, *, force: bool = False) -> Dict[int, str]:
        return {}

    def get_killstreaks(self, *, force: bool = False) -> Dict[int, str]:
        return {}

    def get_wears(self, *, force: bool = False) -> Dict[int, str]:
        return {}

    def get_crateseries(self, *, force: bool = False) -> Dict[int, int]:
        return {}

    def get_craftWeapons(self, *, force: bool = False) -> Dict[int, str]:
        return {}

    def get_uncraftWeapons(self, *, force: bool = False) -> Dict[int, str]:
        return {}
