#!/usr/bin/env python
"""List warpaints used in cached inventories."""

from __future__ import annotations

import json
from pathlib import Path

from utils.inventory.extractors_paint_and_wear import _extract_paintkit
from utils import local_data


BASE_DIR = Path(__file__).resolve().parent.parent


def load_schema() -> tuple[dict[int, str], dict[int, dict]]:
    """Return warpaint names and item schema maps."""
    with (BASE_DIR / "cache" / "schema" / "warpaints.json").open() as f:
        warpaints = json.load(f)
    paint_names_by_id = {int(v): k for k, v in warpaints.items()}

    with (BASE_DIR / "cache" / "schema" / "items.json").open() as f:
        items = json.load(f)
    items_by_defindex = {
        int(item.get("defindex")): item
        for item in items
        if isinstance(item, dict) and str(item.get("defindex", "")).isdigit()
    }

    # Update globals for _extract_paintkit
    local_data.PAINTKIT_NAMES = {str(k): v for k, v in warpaints.items()}
    local_data.PAINTKIT_NAMES_BY_ID = {str(v): k for k, v in warpaints.items()}

    return paint_names_by_id, items_by_defindex


def iter_inventory_items() -> list[dict]:
    """Yield all items from files under ``cached_inventories``."""
    inv_dir = BASE_DIR / "cached_inventories"
    for path in sorted(inv_dir.glob("*.json")):
        try:
            with path.open() as f:
                data = json.load(f)
        except Exception:
            continue
        for item in data.get("items", []):
            yield item


def main() -> int:
    paint_by_id, items_by_defindex = load_schema()

    for asset in iter_inventory_items():
        defindex = asset.get("defindex")
        try:
            defindex = int(defindex)
        except (TypeError, ValueError):
            defindex = None
        schema_entry = (
            items_by_defindex.get(defindex, {}) if defindex is not None else {}
        )
        warpaint_id, paint_name = _extract_paintkit(asset, schema_entry)
        if warpaint_id is not None:
            name = paint_by_id.get(warpaint_id) or paint_name
        else:
            name = None
        weapon = schema_entry.get("item_name") or schema_entry.get("name")

        if not name:
            name = "Unknown Warpaint"
        if not weapon:
            weapon = "Unknown Weapon"

        print(f"{name} {weapon}")

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())
