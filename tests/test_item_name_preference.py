from utils import inventory_processor as ip
from utils import schema_fetcher as sf
from utils import items_game_cache as ig


def test_enrich_inventory_prefers_items_game(monkeypatch):
    sf.SCHEMA = {"111": {"defindex": 111, "item_name": "Wrong", "image_url": "i"}}
    monkeypatch.setattr(
        ig, "ensure_items_game_cached", lambda: {"items": {"111": {"name": "Correct"}}}
    )
    monkeypatch.setattr(ig, "ITEM_BY_DEFINDEX", {"111": {"name": "Correct"}}, False)
    data = {"items": [{"defindex": 111, "quality": 6}]}
    items = ip.enrich_inventory(data)
    assert items[0]["name"].endswith("Correct")
