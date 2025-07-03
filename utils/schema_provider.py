from __future__ import annotations

from typing import Any, Dict

import requests


class SchemaProvider:
    """Fetch and cache TF2 schema properties from schema.autobot.tf."""

    def __init__(self, base_url: str = "https://schema.autobot.tf") -> None:
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self.cache_effects_by_id: Dict[int, str] | None = None
        self.cache_paints_by_id: Dict[int, str] | None = None
        self.cache_paintkits_by_id: Dict[int, str] | None = None
        self.cache_killstreaks_by_id: Dict[int, str] | None = None
        self.cache_wears_by_id: Dict[int, str] | None = None
        self.cache_qualities_by_id: Dict[int, str] | None = None
        self.cache_defindexes_by_id: Dict[int, str] | None = None
        self.cache_crateseries_by_id: Dict[int, int] | None = None
        self.cache_strangeParts_by_id: Dict[str, str] | None = None
        self.cache_craftWeapons_by_id: Dict[int, str] | None = None
        self.cache_uncraftWeapons_by_id: Dict[int, str] | None = None

    def _fetch(self, endpoint: str) -> Any:
        url = f"{self.base_url}{endpoint}"
        r = self._session.get(url, timeout=20)
        r.raise_for_status()
        return r.json()

    def get_effects(self) -> Dict[int, str]:
        if self.cache_effects_by_id is None:
            data = self._fetch("/properties/effects")
            self.cache_effects_by_id = {
                int(v): k for k, v in data.items() if isinstance(v, int)
            }
        return self.cache_effects_by_id

    def get_paints(self) -> Dict[int, str]:
        if self.cache_paints_by_id is None:
            data = self._fetch("/properties/paints")
            self.cache_paints_by_id = {
                int(v): k for k, v in data.items() if isinstance(v, int)
            }
        return self.cache_paints_by_id

    def get_paintkits(self) -> Dict[int, str]:
        if self.cache_paintkits_by_id is None:
            data = self._fetch("/properties/paintkits")
            self.cache_paintkits_by_id = {
                int(v): k for k, v in data.items() if isinstance(v, int)
            }
        return self.cache_paintkits_by_id

    def get_killstreaks(self) -> Dict[int, str]:
        if self.cache_killstreaks_by_id is None:
            data = self._fetch("/properties/killstreaks")
            self.cache_killstreaks_by_id = {
                int(k): v for k, v in data.items() if str(k).isdigit()
            }
        return self.cache_killstreaks_by_id

    def get_wears(self) -> Dict[int, str]:
        if self.cache_wears_by_id is None:
            data = self._fetch("/properties/wears")
            self.cache_wears_by_id = {
                int(k): v for k, v in data.items() if str(k).isdigit()
            }
        return self.cache_wears_by_id

    def get_qualities(self) -> Dict[int, str]:
        if self.cache_qualities_by_id is None:
            data = self._fetch("/properties/qualities")
            self.cache_qualities_by_id = {
                int(v): k for k, v in data.items() if isinstance(v, int)
            }
        return self.cache_qualities_by_id

    def get_defindexes(self) -> Dict[int, str]:
        if self.cache_defindexes_by_id is None:
            data = self._fetch("/properties/defindexes")
            self.cache_defindexes_by_id = {
                int(k): v for k, v in data.items() if str(k).isdigit()
            }
        return self.cache_defindexes_by_id

    def get_crateseries(self) -> Dict[int, int]:
        if self.cache_crateseries_by_id is None:
            data = self._fetch("/properties/crateseries")
            self.cache_crateseries_by_id = {
                int(k): int(v)
                for k, v in data.items()
                if str(k).isdigit() and str(v).isdigit()
            }
        return self.cache_crateseries_by_id

    def get_strangeParts(self) -> Dict[str, str]:
        if self.cache_strangeParts_by_id is None:
            data = self._fetch("/properties/strangeParts")
            self.cache_strangeParts_by_id = {
                v: k for k, v in data.items() if isinstance(v, str)
            }
        return self.cache_strangeParts_by_id

    def get_craftWeapons(self) -> Dict[int, str]:
        if self.cache_craftWeapons_by_id is None:
            data = self._fetch("/properties/craftWeapons")
            mapping: Dict[int, str] = {}
            if isinstance(data, list):
                for sku in data:
                    try:
                        defindex = int(str(sku).split(";")[0])
                    except (ValueError, IndexError):
                        continue
                    mapping[defindex] = sku
            self.cache_craftWeapons_by_id = mapping
        return self.cache_craftWeapons_by_id

    def get_uncraftWeapons(self) -> Dict[int, str]:
        if self.cache_uncraftWeapons_by_id is None:
            data = self._fetch("/properties/uncraftWeapons")
            mapping: Dict[int, str] = {}
            if isinstance(data, list):
                for sku in data:
                    try:
                        defindex = int(str(sku).split(";")[0])
                    except (ValueError, IndexError):
                        continue
                    mapping[defindex] = sku
            self.cache_uncraftWeapons_by_id = mapping
        return self.cache_uncraftWeapons_by_id
