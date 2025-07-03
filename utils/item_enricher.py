from __future__ import annotations

from typing import Any, Dict, List
import logging

from .schema_provider import SchemaProvider


class ItemEnricher:
    """Simple inventory enrichment using :class:`SchemaProvider`."""

    SPELL_NAMES = {
        "Halloween Fire",
        "Exorcism",
        "Pumpkin Bombs",
        "Gourd Grenades",
        "Squash Rockets",
        "Sentry Quad-Pumpkins",
    }

    def __init__(self, provider: SchemaProvider | None = None) -> None:
        self.provider = provider or SchemaProvider()
        self._spell_effect_ids: set[int] | None = None
        self._logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    def _load_spell_effect_ids(self) -> set[int]:
        if self._spell_effect_ids is None:
            mapping = self.provider.get_effects()
            self._spell_effect_ids = {
                eid for eid, name in mapping.items() if name in self.SPELL_NAMES
            }
        return self._spell_effect_ids

    # ------------------------------------------------------------------
    def _enrich_attributes(self, attributes: list) -> Dict[str, Any]:
        """Return attribute info extracted from ``attributes``."""

        result = {
            "unusual_effect": None,
            "paint": None,
            "killstreak_tier": None,
            "sheen": None,
            "killstreaker": None,
            "strange_parts": [],
            "paintkit": None,
        }

        paints = self.provider.get_paints()
        killstreaks = self.provider.get_killstreaks()
        effects = self.provider.get_effects()
        paintkits = self.provider.get_paintkits()
        strange_parts = self.provider.get_strangeParts()
        spell_ids = self._load_spell_effect_ids()

        for attr in attributes or []:
            try:
                idx = int(attr.get("defindex", 0))
            except (TypeError, ValueError):
                continue

            val_raw = (
                attr.get("float_value") if "float_value" in attr else attr.get("value")
            )
            try:
                val = int(float(val_raw)) if val_raw is not None else None
            except (TypeError, ValueError):
                val = None

            if idx == 142 and val is not None:
                result["paint"] = paints.get(val) or paints.get(str(val))
                if val and result["paint"] is None:
                    self._logger.warning("Unknown paint id: %s", val)
            elif idx == 2025 and val is not None:
                result["killstreak_tier"] = killstreaks.get(val) or killstreaks.get(
                    str(val)
                )
                if val and result["killstreak_tier"] is None:
                    self._logger.warning("Unknown killstreak tier id: %s", val)
            elif idx == 2013 and val is not None:
                result["sheen"] = effects.get(val) or effects.get(str(val))
                if val and result["sheen"] is None:
                    self._logger.warning("Unknown sheen effect id: %s", val)
            elif idx == 2014 and val is not None:
                result["killstreaker"] = effects.get(val) or effects.get(str(val))
                if val and result["killstreaker"] is None:
                    self._logger.warning("Unknown killstreaker id: %s", val)
            elif idx == 134 and val is not None:
                if val not in spell_ids:
                    result["unusual_effect"] = effects.get(val) or effects.get(str(val))
                    if val and result["unusual_effect"] is None:
                        self._logger.warning("Unknown unusual effect id: %s", val)
            elif idx == 834 and val is not None:
                result["paintkit"] = paintkits.get(val) or paintkits.get(str(val))
                if val and result["paintkit"] is None:
                    self._logger.warning("Unknown paintkit id: %s", val)

            if str(idx) in strange_parts:
                name = strange_parts[str(idx)]
                if name not in result["strange_parts"]:
                    result["strange_parts"].append(name)

        return result

    # ------------------------------------------------------------------
    def enrich_inventory(self, raw_items: List[dict]) -> List[Dict[str, Any]]:
        """Return list of item dicts enriched with schema data."""

        defindexes = self.provider.get_defindexes()
        qualities = self.provider.get_qualities()

        enriched: List[Dict[str, Any]] = []
        for item in raw_items:
            defindex = int(item.get("defindex", 0))
            quality = int(item.get("quality", 0))
            attrs = item.get("attributes", [])
            name = defindexes.get(defindex) or defindexes.get(str(defindex))
            if name is None:
                self._logger.warning("Unknown defindex %s", defindex)
            quality_name = qualities.get(quality) or qualities.get(str(quality))
            if quality_name is None:
                self._logger.warning("Unknown quality id %s", quality)
            info = {
                "id": item.get("id"),
                "defindex": defindex,
                "original_id": item.get("original_id"),
                "inventory": item.get("inventory"),
                "name": name,
                "quality": quality_name,
            }
            info.update(self._enrich_attributes(attrs))
            enriched.append(info)
        return enriched
