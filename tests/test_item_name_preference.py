from utils import inventory_processor as ip
from utils import local_data as ld


def test_enrich_inventory_prefers_items_game(monkeypatch):
    ld.TF2_SCHEMA = {"111": {"defindex": 111, "item_name": "Wrong", "image_url": "i"}}
    ld.ITEMS_GAME_CLEANED = {"111": {"name": "Correct"}}
    data = {"items": [{"defindex": 111, "quality": 6}]}
    items = ip.enrich_inventory(data)
    assert items[0]["name"].endswith("Correct")
