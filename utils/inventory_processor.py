"""Backward-compatible inventory processing API.

Historically, callers imported enrichment helpers from
``utils.inventory_processor``. The implementation now lives in
``utils.inventory`` modules, but this shim preserves public symbols and
monkeypatch behavior used by tests and external scripts.

The wrapper functions below intentionally call ``get_valuation_service()``
from *this* module's namespace so that tests can monkeypatch
``inventory_processor.get_valuation_service`` and have the patch take effect.
"""

from __future__ import annotations
from typing import Any, Dict, List

from .valuation_service import ValuationService, get_valuation_service
from .inventory.api import (
    enrich_inventory as _api_enrich_inventory,
    process_inventory as _api_process_inventory,
    run_enrichment_test,
)
from .inventory.extractors_paint_and_wear import _extract_paintkit
from .inventory.maps_and_constants import QUALITY_MAP


def enrich_inventory(
    data: Dict[str, Any],
    valuation_service: ValuationService | None = None,
) -> List[Dict[str, Any]]:
    if valuation_service is None:
        valuation_service = get_valuation_service()
    return _api_enrich_inventory(data, valuation_service)


def process_inventory(
    data: Dict[str, Any],
    valuation_service: ValuationService | None = None,
) -> List[Dict[str, Any]]:
    if valuation_service is None:
        valuation_service = get_valuation_service()
    return _api_process_inventory(data, valuation_service)


__all__ = [
    "QUALITY_MAP",
    "_extract_paintkit",
    "enrich_inventory",
    "process_inventory",
    "run_enrichment_test",
    "get_valuation_service",
]
