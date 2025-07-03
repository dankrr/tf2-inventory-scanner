from __future__ import annotations

import json
import os

import argparse
from dotenv import load_dotenv
from utils.item_enricher import ItemEnricher
from utils.inventory_provider import InventoryProvider
from utils.schema_provider import SchemaProvider

load_dotenv()


def main() -> None:
    """Demonstrate inventory enrichment for a single Steam user."""

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--refresh-schema", action="store_true")
    args, _ = parser.parse_known_args()

    if args.refresh_schema:
        SchemaProvider().refresh_all()
        print("\N{CHECK MARK} Schema refreshed")
        return

    steamid = "76561198177872379"  # hardcoded ID for testing

    try:
        schema = SchemaProvider()
        inventory_provider = InventoryProvider(os.getenv("STEAM_API_KEY"))
        enricher = ItemEnricher(schema)

        raw_items = inventory_provider.get_inventory(steamid)
    except Exception as exc:  # network errors, private inventory, etc.
        print(f"Failed to fetch inventory for {steamid}: {exc}")
        return

    enriched = enricher.enrich_inventory(raw_items)

    for item in enriched[:55]:
        print(json.dumps(item, indent=2))


if __name__ == "__main__":
    main()
