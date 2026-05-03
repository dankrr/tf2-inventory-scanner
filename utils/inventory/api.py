from __future__ import annotations

import asyncio
from typing import Any, Dict, List
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
from .. import cdn_image_cache as _cdn_cache
from ..cdn_image_resolver import (
    build_market_hash_name,
    cdn_url,
    resolve_icon_hash,
    is_resolver_enabled,
)


def _get_cdn_cache_key(item: Dict[str, Any]) -> str | None:
    """Return the deterministic cache key for an item variant, or None for plain items."""

    defindex = item.get("defindex")
    try:
        defindex_int = int(defindex) if defindex is not None else None
    except (TypeError, ValueError):
        return None

    if item.get("is_australium") and defindex_int is not None:
        return _cdn_cache.cache_key_australium(defindex_int)

    if item.get("is_war_paint_tool"):
        paintkit_id = item.get("paintkit_id")
        wear_id = item.get("wear_id")
        if paintkit_id is not None and wear_id is not None:
            try:
                return _cdn_cache.cache_key_war_paint_tool(
                    int(paintkit_id), int(wear_id)
                )
            except (TypeError, ValueError):
                pass
        return None

    if item.get("is_skin"):
        paintkit_id = item.get("paintkit_id")
        wear_id = item.get("wear_id")
        if defindex_int is not None and paintkit_id is not None and wear_id is not None:
            try:
                return _cdn_cache.cache_key_war_painted(
                    defindex_int, int(paintkit_id), int(wear_id)
                )
            except (TypeError, ValueError):
                pass

    return None


def _build_hash_name_for_item(item: Dict[str, Any]) -> str | None:
    """Return the Steam Market hash name for a variant item."""

    if item.get("is_australium"):
        return build_market_hash_name(
            is_australium=True,
            base_name=item.get("base_name"),
        )

    paintkit_name = item.get("paintkit_name")
    wear_name = item.get("wear_name")

    if item.get("is_war_paint_tool"):
        return build_market_hash_name(
            is_war_paint_tool=True,
            paintkit_name=paintkit_name,
            wear_name=wear_name,
        )

    if item.get("is_skin"):
        return build_market_hash_name(
            paintkit_name=paintkit_name,
            base_name=item.get("base_name"),
            wear_name=wear_name,
        )

    return None


async def _resolve_cdn_images(items: List[Dict[str, Any]]) -> None:
    """Resolve CDN image URLs for variant items in-place, batching network calls."""

    if not is_resolver_enabled():
        return

    # Map cache_key -> [item indices] that need it
    key_to_indices: Dict[str, List[int]] = {}
    key_to_hash_name: Dict[str, str] = {}

    for idx, item in enumerate(items):
        cache_key = _get_cdn_cache_key(item)
        if cache_key is None:
            continue

        cached = _cdn_cache.get(cache_key)
        if cached:
            item["image_url"] = cdn_url(cached)
            continue

        hash_name = _build_hash_name_for_item(item)
        if hash_name is None:
            continue

        key_to_indices.setdefault(cache_key, []).append(idx)
        key_to_hash_name[cache_key] = hash_name

    if not key_to_indices:
        return

    async with __import__("httpx").AsyncClient() as client:
        tasks = {
            cache_key: asyncio.create_task(resolve_icon_hash(client, hash_name))
            for cache_key, hash_name in key_to_hash_name.items()
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    for cache_key, result in zip(tasks.keys(), results):
        if isinstance(result, Exception) or not result:
            continue
        icon_hash: str = result
        _cdn_cache.put(cache_key, icon_hash)
        url = cdn_url(icon_hash)
        for idx in key_to_indices.get(cache_key, []):
            items[idx]["image_url"] = url


def enrich_inventory(
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

    return items


async def enrich_inventory_async(
    data: Dict[str, Any],
    valuation_service: ValuationService | None = None,
) -> List[Dict[str, Any]]:
    """Like :func:`enrich_inventory` but also resolves CDN images for variant items."""
    items = enrich_inventory(data, valuation_service)
    await _resolve_cdn_images(items)
    return items


def process_inventory(
    data: Dict[str, Any],
    valuation_service: ValuationService | None = None,
) -> List[Dict[str, Any]]:
    """Return enriched items sorted by descending price."""
    if valuation_service is None:
        valuation_service = get_valuation_service()
    items = enrich_inventory(data, valuation_service)

    def _sort_key(item: Dict[str, Any]) -> tuple[float, str]:
        price_info = item.get("price") or {}
        value = price_info.get("value_raw", 0) or 0
        return -float(value), item["name"]

    return sorted(items, key=_sort_key)


async def process_inventory_async(
    data: Dict[str, Any],
    valuation_service: ValuationService | None = None,
) -> List[Dict[str, Any]]:
    """Like :func:`process_inventory` but also resolves CDN images for variant items."""
    if valuation_service is None:
        valuation_service = get_valuation_service()
    items = await enrich_inventory_async(data, valuation_service)

    def _sort_key(item: Dict[str, Any]) -> tuple[float, str]:
        price_info = item.get("price") or {}
        value = price_info.get("value_raw", 0) or 0
        return -float(value), item["name"]

    return sorted(items, key=_sort_key)


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

    items = process_inventory(raw)
    print(json.dumps(items, indent=2))


__all__ = [
    "enrich_inventory",
    "enrich_inventory_async",
    "process_inventory",
    "process_inventory_async",
    "run_enrichment_test",
    "get_valuation_service",
]
