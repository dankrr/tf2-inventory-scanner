from __future__ import annotations

import json
import os

from utils.item_enricher import ItemEnricher
from utils.inventory_provider import InventoryProvider
from utils.schema_provider import SchemaProvider


def main() -> None:
    """Demonstrate inventory enrichment for a single Steam user."""

    steamid = "76561198034324614"  # hardcoded ID for testing

    try:
        schema = SchemaProvider()
        inventory_provider = InventoryProvider(os.getenv("STEAM_API_KEY"))
        enricher = ItemEnricher(schema)

        raw_items = inventory_provider.get_inventory(steamid)
    except Exception as exc:  # network errors, private inventory, etc.
        print(f"Failed to fetch inventory for {steamid}: {exc}")
        return

    enriched = enricher.enrich_inventory(raw_items)

    for item in enriched[:3]:
        print(json.dumps(item, indent=2))


if __name__ == "__main__":
    main()
