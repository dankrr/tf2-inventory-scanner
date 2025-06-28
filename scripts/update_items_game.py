"""Refresh the cached items_game data from SteamDatabase."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path


def main() -> None:
    """Fetch and preprocess items_game.txt into JSON."""

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))

    from utils import items_game_cache  # local import after path tweak
    from utils import local_data

    logging.basicConfig(level=logging.INFO)
    data = items_game_cache.update_items_game()
    cleaned = local_data.clean_items_game(data)
    dest = root / "data/items_game_cleaned.json"
    dest.write_text(json.dumps(cleaned))
    print(f"Fetched {len(data.get('items', {}))} items")
    print(f"Wrote {len(cleaned)} cleaned items to {dest}")


if __name__ == "__main__":
    main()
