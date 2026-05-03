from typing import Any, Dict, List
import asyncio
import json
from pathlib import Path

from .. import local_data

# Prefer the canonical valuation service module but fall back to older paths.
try:  # pragma: no cover - import shim
    from ..valuation_service import ValuationService, get_valuation_service
except Exception:  # pragma: no cover
    try:
        from ..services.valuation_service import (  # type: ignore
            ValuationService,
            get_valuation_service,
        )
    except Exception:  # pragma: no cover
        from services.valuation_service import (  # type: ignore
            ValuationService,
            get_valuation_service,
        )
from .processor import _process_item
from .extractors_misc import _PARTS_BY_ID
from ..cdn_image_resolver import CDNImageResolver, is_enabled


async def enrich_inventory_async(
    data: Dict[str, Any],
    valuation_service: ValuationService | None = None,
) -> List[Dict[str, Any]]:
    """Return a list of inventory items enriched with schema info.

    Parameters
    ----------
    data:
        Inventory payload from Steam.
    valuation_service:
        Optional :class:`ValuationService` used to look up prices. Defaults to
        :func:`~utils.valuation_service.get_valuation_service`, which provides
        a singleton service.
    """
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
                all_parts = set(existing) | parts_found
                item["strange_parts"] = sorted(all_parts)

        spells_raw = item.get("spells", [])
        if isinstance(spells_raw, dict):
            spells_list = spells_raw.get("list", [])
        elif isinstance(spells_raw, list):
            spells_list = spells_raw
        else:
            spells_list = []

        item["modal_spells"] = spells_list
        item["spells"] = spells_list  # backward compatibility for JS
        items.append(item)

    if is_enabled() and items:
        resolver = CDNImageResolver()
        semaphore = asyncio.Semaphore(4)

        async def _resolve_and_patch(item: Dict[str, Any]) -> None:
            async with semaphore:
                resolved = await resolver.resolve_item_image(item)
            if resolved:
                item["image_url"] = resolved

        await asyncio.gather(*[_resolve_and_patch(item) for item in items])

    return items


async def process_inventory_async(
    data: Dict[str, Any],
    valuation_service: ValuationService | None = None,
) -> List[Dict[str, Any]]:
    """Return enriched items sorted by descending price."""
    if valuation_service is None:
        valuation_service = get_valuation_service()
    items = await enrich_inventory_async(data, valuation_service)

    def _sort_key(item: Dict[str, Any]) -> tuple[float, str]:
        price_info = item.get("price") or {}
        value = price_info.get("value_raw", 0) or 0
        return -float(value), item["name"]

    return sorted(items, key=_sort_key)


def enrich_inventory(
    data: Dict[str, Any],
    valuation_service: ValuationService | None = None,
) -> List[Dict[str, Any]]:
    """Synchronous wrapper around :func:`enrich_inventory_async`."""

    return asyncio.run(enrich_inventory_async(data, valuation_service))


def process_inventory(
    data: Dict[str, Any],
    valuation_service: ValuationService | None = None,
) -> List[Dict[str, Any]]:
    """Synchronous wrapper around :func:`process_inventory_async`."""

    return asyncio.run(process_inventory_async(data, valuation_service))


def run_enrichment_test(path: str | None = None) -> None:
    """Load a local inventory JSON file, enrich it, and print the result.

    This helper is intended for manual debugging of the enrichment logic. It
    loads ``converted.json`` next to this module (or the file provided via
    ``path``), processes the inventory with :func:`process_inventory`, and
    prints the enriched items as pretty JSON.
    """

    if path is None:
        file_path = Path(__file__).with_name("converted.json")
    else:
        file_path = Path(path)

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    local_data.load_files(verbose=True)
    with file_path.open() as f:
        raw = json.load(f)

    items = asyncio.run(process_inventory_async(raw))
    print(json.dumps(items, indent=2))


__all__ = [
    "enrich_inventory_async",
    "process_inventory_async",
    "enrich_inventory",
    "process_inventory",
    "run_enrichment_test",
    "get_valuation_service",
]
