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

    logging.basicConfig(level=logging.INFO)
    data = items_game_cache.update_items_game()
    dest = (root / "cache/items_game_cleaned.json").resolve()
    dest.write_text(json.dumps(data))
    print(f"Fetched {len(data.get('items', {}))} cleaned items to {dest}")


if __name__ == "__main__":
    main()
