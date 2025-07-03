from __future__ import annotations

from typing import Any, Dict, List
import logging

from .schema_provider import SchemaProvider


class ItemEnricher:
    """Simple inventory enrichment using :class:`SchemaProvider`."""

    def __init__(self, provider: SchemaProvider | None = None) -> None:
        self.provider = provider or SchemaProvider()
        self.items = self.provider.get_items()
        self.attrs = self.provider.get_attributes()
        self.effects = self.provider.get_effects()
        self.parts = self.provider.get_strange_parts()
        self.paints_val = {v: k for k, v in self.provider.get_paints().items()}
        self.qualities = {v: k for k, v in self.provider.get_qualities().items()}
        self._logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    def _wear_label(self, wear: float) -> str:
        if wear < 0.07:
            return "Factory New"
        if wear < 0.15:
            return "Minimal Wear"
        if wear < 0.38:
            return "Field-Tested"
        if wear < 0.45:
            return "Well-Worn"
        return "Battle Scarred"

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
        }

        for attr in attributes or []:
            try:
                aid = int(attr.get("defindex", 0))
            except (TypeError, ValueError):
                continue

            val = attr.get("float_value") or attr.get("value")

            info = self.attrs.get(aid, {})
            cls = info.get("class", "")
            name = info.get("name", "")

            if aid in self.parts:
                part = self.parts[aid]
                if part not in result["strange_parts"]:
                    result["strange_parts"].append(part)
                continue

            if cls == "set_item_tint_rgb" and isinstance(val, int):
                result["paint"] = self.paints_val.get(val)
            elif cls.startswith("set_attached_particle") and isinstance(val, int):
                result["unusual_effect"] = self.effects.get(val)
            elif name == "killstreak tier":
                tier_map = {
                    1: "Killstreak",
                    2: "Specialized Killstreak",
                    3: "Professional Killstreak",
                }
                result["killstreak_tier"] = tier_map.get(int(val), f"Tier {val}")
            elif name == "killstreak sheen":
                result["sheen"] = self.effects.get(int(val)) or f"Sheen {val}"
            elif name == "killstreak effect":
                result["killstreaker"] = self.effects.get(int(val))
            elif cls == "set_item_texture_wear":
                try:
                    w = float(val)
                except (TypeError, ValueError):
                    continue
                result["wear_float"] = round(w, 3)
                result["wear_label"] = self._wear_label(w)

        return result

    # ------------------------------------------------------------------
    def enrich_inventory(self, raw_items: List[dict]) -> List[Dict[str, Any]]:
        """Return list of item dicts enriched with schema data."""

        defindexes = self.items
        qualities = self.qualities

        enriched: List[Dict[str, Any]] = []
        for item in raw_items:
            defindex = int(item.get("defindex", 0))
            quality = int(item.get("quality", 0))
            attrs = item.get("attributes", [])
            entry = defindexes.get(defindex) or {}
            name = entry.get("item_name") or entry.get("name")
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
