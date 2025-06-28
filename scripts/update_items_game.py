import logging
from utils import items_game_cache

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = items_game_cache.update_items_game()
    print(f"Fetched {len(data.get('items', {}))} items")
