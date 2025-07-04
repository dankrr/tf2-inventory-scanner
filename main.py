from __future__ import annotations

import json
import os

import argparse
from dotenv import load_dotenv
from utils.item_enricher import ItemEnricher
from utils.inventory_provider import InventoryProvider
from utils.schema_provider import SchemaProvider
from utils import local_data

load_dotenv()


def main() -> None:
    """Demonstrate inventory enrichment for a single Steam user."""

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("steamid", nargs="?")
    args, _ = parser.parse_known_args()

    if args.refresh:
        SchemaProvider().refresh_all(verbose=args.verbose)
        print("\N{CHECK MARK} Schema refreshed")
        return

    local_data.load_files()

    schema = SchemaProvider()
    enricher = ItemEnricher(schema)

    raw_items = None
    steamid = args.steamid
    if not steamid:
        if input("Load cached inventory? [y/N] ").strip().lower().startswith("y"):
            path = input("Path to JSON file: ").strip()
            try:
                with open(path) as f:
                    raw_items = json.load(f)
            except Exception as exc:
                print(f"Failed to load {path}: {exc}")
                return
        else:
            steamid = input("Steam64 ID: ").strip()

    if raw_items is None:
        try:
            inventory_provider = InventoryProvider(os.getenv("STEAM_API_KEY"))
            raw_items = inventory_provider.get_inventory(steamid)
        except Exception as exc:  # network errors, private inventory, etc.
            print(f"Failed to fetch inventory for {steamid}: {exc}")
            return
        if not args.steamid and input(
            "Cache inventory? [y/N] "
        ).strip().lower().startswith("y"):
            from pathlib import Path

            cache_dir = Path("cached_inventories")
            cache_dir.mkdir(exist_ok=True)
            (cache_dir / f"{steamid}.json").write_text(json.dumps(raw_items))

    enriched = enricher.enrich_inventory(raw_items)

    for item in enriched[:100]:
        print(json.dumps(item, indent=2))


if __name__ == "__main__":
    main()
