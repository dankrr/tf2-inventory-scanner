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
        "attributes": "/raw/schema/attributes",
        "particles": "/raw/schema/attribute_controlled_attached_particles",
        "effects": "/properties/effects",
        "paints": "/properties/paints",
        "origins": "/raw/schema/originNames",
        "parts": "/properties/strangeParts",
        "paintkits": "/properties/paintkits",
        "qualities": "/properties/qualities",
        "defindexes": "/properties/defindexes",
        "string_lookups": "/raw/schema/string_lookups",
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
        self.effects_by_index: Dict[int, Any] | None = None
        self.parts_by_defindex: Dict[int, Any] | None = None
        self.paints_map: Dict[str, int] | None = None
        self.paintkits_map: Dict[int, str] | None = None
        self.qualities_map: Dict[str, int] | None = None
        self.defindex_names: Dict[int, str] | None = None
        self.origins_by_index: Dict[int, str] | None = None
        self.string_lookups: Dict[str, str] | None = None

    # ------------------------------------------------------------------
    def _fetch(self, endpoint: str) -> Any:
        url = f"{self.base_url}{endpoint}"
        resp = self._session.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def _cache_file(self, key: str) -> Path:
        if key == "paintkits":
            return self.cache_dir / "warpaints.json"
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
            if (
                key == "effects"
                and isinstance(data, dict)
                and not any(str(k).isdigit() for k in data)
                and all(str(v).isdigit() for v in data.values())
            ):
                # convert mapping of name -> id to id -> name
                data = {int(v): k for k, v in data.items()}
            path.write_text(json.dumps(data, indent=2))
        elif isinstance(data, dict) and "value" in data:
            # migrate old cache format that stores entire API response
            data = data["value"]
            path.write_text(json.dumps(data, indent=2))
        return data

    # ------------------------------------------------------------------
    def _unwrap_and_index(self, data: Any, key_field: str) -> Dict[int, Any]:
        if isinstance(data, dict) and "value" in data:
            data = data["value"]
        if isinstance(data, list):
            return {
                int(e[key_field]): e
                for e in data
                if isinstance(e, dict) and key_field in e
            }
        if isinstance(data, dict):
            numeric = {int(k): v for k, v in data.items() if str(k).isdigit()}
            if numeric:
                return numeric
            return {
                int(v[key_field]): v
                for v in data.values()
                if isinstance(v, dict) and key_field in v
            }
        return {}

    # ------------------------------------------------------------------
    def refresh_all(self, verbose: bool = False) -> None:
        """Force refresh of all schema files."""
        for key, ep in self.ENDPOINTS.items():
            if verbose:
                print(f"Fetching {key}...")
            data = self._load(key, ep, force=True)
            count = len(data) if hasattr(data, "__len__") else 0
            if verbose:
                path = self._cache_file(key)
                print(f"\N{CHECK MARK} Saved {path} ({count} entries)")

        self.items_by_defindex = None
        self.attributes_by_defindex = None
        self.paints_map = None
        self.paintkits_map = None
        self.parts_by_defindex = None
        self.defindex_names = None
        self.qualities_map = None
        self.effects_by_index = None
        self.origins_by_index = None
        self.string_lookups = None

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
            self.items_by_defindex = self._unwrap_and_index(data, "defindex")
        return self.items_by_defindex

    def get_attributes(self, *, force: bool = False) -> Dict[int, Any]:
        if self.attributes_by_defindex is None or force:
            data = self._load("attributes", self.ENDPOINTS["attributes"], force)
            self.attributes_by_defindex = self._unwrap_and_index(data, "defindex")
        return self.attributes_by_defindex

    def _from_name_map(self, data: dict) -> Dict[int, str]:
        mapping: Dict[int, str] = {}
        for k, v in data.items():
            if str(k).isdigit():
                mapping[int(k)] = str(v)
            elif str(v).isdigit():
                mapping[int(v)] = str(k)
        return mapping

    def get_effects(self, *, force: bool = False) -> Dict[int, Any]:
        if self.effects_by_index is None or force:
            data = self._load("effects", self.ENDPOINTS["effects"], force)
            mapping = self._unwrap_and_index(data, "id")
            if mapping and all(not isinstance(v, dict) for v in mapping.values()):
                mapping = {
                    idx: {"id": idx, "name": str(name)} for idx, name in mapping.items()
                }
            self.effects_by_index = mapping
        return self.effects_by_index

    def get_paints(self, *, force: bool = False) -> Dict[str, int]:
        if self.paints_map is None or force:
            data = self._load("paints", self.ENDPOINTS["paints"], force)
            if isinstance(data, dict) and "value" in data:
                data = data["value"]
            if isinstance(data, list):
                self.paints_map = {
                    str(e["name"]): int(e["id"])
                    for e in data
                    if isinstance(e, dict) and "name" in e and "id" in e
                }
            else:
                self.paints_map = {
                    str(name): int(val)
                    for name, val in data.items()
                    if str(val).isdigit()
                }
        return self.paints_map

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

    def get_string_lookups(self, *, force: bool = False) -> Dict[str, str]:
        if self.string_lookups is None or force:
            data = self._load("string_lookups", self.ENDPOINTS["string_lookups"], force)
            if isinstance(data, dict) and "value" in data:
                data = data["value"]
            if isinstance(data, list):
                self.string_lookups = {
                    str(e.get("key")): str(e.get("value"))
                    for e in data
                    if isinstance(e, dict) and "key" in e and "value" in e
                }
            elif isinstance(data, dict):
                self.string_lookups = {str(k): str(v) for k, v in data.items()}
            else:
                self.string_lookups = {}
        return self.string_lookups

    def get_parts(self, *, force: bool = False) -> Dict[int, Any]:
        if self.parts_by_defindex is None or force:
            data = self._load("parts", self.ENDPOINTS["parts"], force)
            self.parts_by_defindex = self._unwrap_and_index(data, "id")
        return self.parts_by_defindex

    def get_qualities(self, *, force: bool = False) -> Dict[str, int]:
        if self.qualities_map is None or force:
            data = self._load("qualities", self.ENDPOINTS["qualities"], force)
            if isinstance(data, dict) and "value" in data:
                data = data["value"]
            if isinstance(data, list):
                self.qualities_map = {
                    str(e["name"]): int(e["id"])
                    for e in data
                    if isinstance(e, dict) and "name" in e and "id" in e
                }
            else:
                self.qualities_map = {
                    str(name): int(val)
                    for name, val in data.items()
                    if str(val).isdigit()
                }
        return self.qualities_map

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

    def get_strangeParts(self, *, force: bool = False) -> Dict[int, Any]:
        return self.get_parts(force=force)

    def get_strange_parts(self, *, force: bool = False) -> Dict[int, Any]:
        """Alias for :meth:`get_parts`."""
        return self.get_parts(force=force)

    def get_item_by_defindex(self, defindex: int) -> Dict[str, Any] | None:
        items = self.get_items()
        item = items.get(defindex)
        if item is None:
            self._logger.warning("Defindex %s not found in schema", defindex)
        return item

    # Stub helpers kept for backward compatibility --------------------------
    def get_paintkits(self, *, force: bool = False) -> Dict[int, str]:
        if self.paintkits_map is None or force:
            data = self._load("paintkits", self.ENDPOINTS["paintkits"], force)
            if isinstance(data, dict):
                if all(str(v).isdigit() for v in data.values()):
                    mapping = {int(v): str(k) for k, v in data.items()}
                else:
                    mapping = {
                        int(k): str(v) for k, v in data.items() if str(k).isdigit()
                    }
            else:
                mapping = {}
            self.paintkits_map = mapping
        return self.paintkits_map

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
