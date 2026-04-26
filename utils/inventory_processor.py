"""Backward-compatible inventory processing API.

Historically, callers imported enrichment helpers from
``utils.inventory_processor``. The implementation now lives in
``utils.inventory`` modules, but this shim preserves public symbols and
monkeypatch behavior used by tests and external scripts.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .valuation_service import ValuationService, get_valuation_service
from .inventory.api import run_enrichment_test
from .inventory.processor import _process_item
from .inventory.extractors_misc import _PARTS_BY_ID
from .inventory.extractors_paint_and_wear import _extract_paintkit
from .inventory.maps_and_constants import QUALITY_MAP


def enrich_inventory(
    data: Dict[str, Any],
    valuation_service: ValuationService | None = None,
) -> List[Dict[str, Any]]:
    """Return inventory items enriched with schema, badges, and pricing."""

    if valuation_service is None:
        valuation_service = get_valuation_service()

    items_raw = data.get("items")
    if not isinstance(items_raw, list):
        return []

    items: List[Dict[str, Any]] = []
    for asset in items_raw:
        item = _process_item(asset, valuation_service)
        if not item:
            continue

        quality_flag = item.get("quality")
        if (
            quality_flag == 11
            or quality_flag == "Strange"
            or asset.get("quality") == 11
        ):
            attrs = item.get("attributes")
            if not isinstance(attrs, list):
                attrs = asset.get("attributes", [])
            parts_found: set[str] = set()
            for attr in attrs:
                if attr.get("defindex") == 214:
                    try:
                        idx = int(attr.get("value"))
                    except (TypeError, ValueError):
                        continue
                    name = _PARTS_BY_ID.get(idx)
                    if name:
                        parts_found.add(name)
            if parts_found:
                existing = item.get("strange_parts", [])
                if not isinstance(existing, list):
                    existing = []
                item["strange_parts"] = sorted(set(existing) | parts_found)

        spells_raw = item.get("spells", [])
        if isinstance(spells_raw, dict):
            spells_list = spells_raw.get("list", [])
        elif isinstance(spells_raw, list):
            spells_list = spells_raw
        else:
            spells_list = []
        item["modal_spells"] = spells_list
        item["spells"] = spells_list
        items.append(item)

    return items


def process_inventory(
    data: Dict[str, Any],
    valuation_service: ValuationService | None = None,
) -> List[Dict[str, Any]]:
    """Return enriched items sorted by descending price then item name."""

    if valuation_service is None:
        valuation_service = get_valuation_service()
    items = enrich_inventory(data, valuation_service)
    return sorted(
        items,
        key=lambda item: (
            -float((item.get("price") or {}).get("value_raw", 0) or 0),
            item.get("name", ""),
        ),
    )


__all__ = [
    "QUALITY_MAP",
    "_extract_paintkit",
    "enrich_inventory",
    "process_inventory",
    "run_enrichment_test",
    "get_valuation_service",
]
