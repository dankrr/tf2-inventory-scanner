from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

import requests


class SchemaProvider:
    """Fetch and cache TF2 schema data from schema.autobot.tf."""

    TTL = 48 * 60 * 60  # 48 hours
    ENDPOINTS = {
        "items": "/raw/schema/items",
        "attributes": "/attributes",
        "effects": "/effects",
        "paints": "/paints",
        "origins": "/origins",
        "parts": "/parts",
        "qualities": "/qualities",
        "defindexes": "/properties/defindexes",
    }

    def __init__(
        self,
        base_url: str = "https://schema.autobot.tf",
        cache_dir: str | Path = "schema",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._session = requests.Session()
        self._logger = logging.getLogger(__name__)
        self.items_by_defindex: Dict[int, Any] | None = None
        self.attributes_by_defindex: Dict[int, Any] | None = None
        self.effects_by_index: Dict[int, str] | None = None
        self.paints_by_defindex: Dict[int, str] | None = None
        self.origins_by_index: Dict[int, str] | None = None
        self.parts_by_defindex: Dict[int, str] | None = None
        self.qualities_by_index: Dict[int, str] | None = None
        self.defindex_names: Dict[int, str] | None = None

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
            fetched = self._fetch(endpoint)
            if isinstance(fetched, dict) and "value" in fetched:
                data = fetched["value"]
            else:
                data = fetched
            path.write_text(json.dumps(data))
        elif isinstance(data, dict) and "value" in data:
            # migrate old cache format that stores entire API response
            data = data["value"]
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
                    if key in {"items", "attributes", "paints", "parts", "defindexes"}
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

            mapping: Dict[int, Any] = {}
            if isinstance(data, list):
                for item in data:
                    try:
                        idx = int(item.get("defindex", -1))
                    except (TypeError, ValueError):
                        continue
                    if idx >= 0:
                        mapping[idx] = item
            elif isinstance(data, dict):
                for k, v in data.items():
                    try:
                        idx = int(k)
                    except (TypeError, ValueError):
                        idx = int(v.get("defindex", -1)) if isinstance(v, dict) else -1
                    if idx >= 0:
                        mapping[idx] = v

            self.items_by_defindex = mapping
        return self.items_by_defindex

    def get_attributes(self, *, force: bool = False) -> Dict[int, Any]:
        if self.attributes_by_defindex is None or force:
            data = self._load("attributes", self.ENDPOINTS["attributes"], force)
            mapping: Dict[int, Any] = {}
            if isinstance(data, list):
                for attr in data:
                    try:
                        idx = int(attr.get("defindex", -1))
                    except (TypeError, ValueError):
                        continue
                    if idx >= 0:
                        name = attr.get("name")
                        mapping[idx] = name if name is not None else attr
            elif isinstance(data, dict):
                mapping = self._to_int_map(data)
            self.attributes_by_defindex = mapping
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
            mapping: Dict[int, str] = {}
            if isinstance(data, list):
                for effect in data:
                    try:
                        idx = int(effect.get("id", -1))
                    except (TypeError, ValueError):
                        continue
                    if idx >= 0:
                        name = effect.get("name") or effect.get("effect")
                        if name is not None:
                            mapping[idx] = str(name)
            elif isinstance(data, dict):
                mapping = self._from_name_map(data)
            self.effects_by_index = mapping
        return self.effects_by_index

    def get_paints(self, *, force: bool = False) -> Dict[int, str]:
        if self.paints_by_defindex is None or force:
            data = self._load("paints", self.ENDPOINTS["paints"], force)
            mapping: Dict[int, str] = {}
            if isinstance(data, list):
                for paint in data:
                    try:
                        idx = int(paint.get("id", -1))
                    except (TypeError, ValueError):
                        continue
                    if idx >= 0:
                        name = paint.get("name")
                        if name is not None:
                            mapping[idx] = str(name)
            elif isinstance(data, dict):
                mapping = self._from_name_map(data)
            self.paints_by_defindex = mapping
        return self.paints_by_defindex

    def get_origins(self, *, force: bool = False) -> Dict[int, str]:
        if self.origins_by_index is None or force:
            data = self._load("origins", self.ENDPOINTS["origins"], force)
            mapping: Dict[int, str] = {}
            if isinstance(data, list):
                for origin in data:
                    try:
                        idx = int(origin.get("id", -1))
                    except (TypeError, ValueError):
                        continue
                    if idx >= 0:
                        name = origin.get("name")
                        if name is not None:
                            mapping[idx] = str(name)
            elif isinstance(data, dict):
                mapping = self._from_name_map(data)
            self.origins_by_index = mapping
        return self.origins_by_index

    def get_parts(self, *, force: bool = False) -> Dict[int, str]:
        if self.parts_by_defindex is None or force:
            data = self._load("parts", self.ENDPOINTS["parts"], force)
            mapping: Dict[int, str] = {}
            if isinstance(data, list):
                for part in data:
                    try:
                        idx = int(part.get("id", -1))
                    except (TypeError, ValueError):
                        continue
                    if idx >= 0:
                        name = part.get("name")
                        if name is not None:
                            mapping[idx] = str(name)
            elif isinstance(data, dict):
                mapping = self._from_name_map(data)
            self.parts_by_defindex = mapping
        return self.parts_by_defindex

    def get_qualities(self, *, force: bool = False) -> Dict[int, str]:
        if self.qualities_by_index is None or force:
            data = self._load("qualities", self.ENDPOINTS["qualities"], force)
            mapping: Dict[int, str] = {}
            if isinstance(data, list):
                for qual in data:
                    try:
                        idx = int(qual.get("id", -1))
                    except (TypeError, ValueError):
                        continue
                    if idx >= 0:
                        name = qual.get("name")
                        if name is not None:
                            mapping[idx] = str(name)
            elif isinstance(data, dict):
                mapping = self._from_name_map(data)
            self.qualities_by_index = mapping
        return self.qualities_by_index

    # Compatibility helpers -------------------------------------------------
    def get_defindexes(self, *, force: bool = False) -> Dict[int, Any]:
        if self.defindex_names is None or force:
            data = self._load("defindexes", self.ENDPOINTS["defindexes"], force)
            if isinstance(data, dict):
                self.defindex_names = self._from_name_map(data)
            else:
                # fallback to extracting names from items metadata
                self.defindex_names = {
                    idx: info.get("item_name") or info.get("name") or ""
                    for idx, info in self.get_items(force=force).items()
                }
        return self.defindex_names

    def get_strangeParts(self, *, force: bool = False) -> Dict[int, str]:
        return self.get_parts(force=force)

    def get_item_by_defindex(self, defindex: int) -> Dict[str, Any] | None:
        items = self.get_items()
        item = items.get(defindex)
        if item is None:
            self._logger.warning("Defindex %s not found in schema", defindex)
        return item

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
