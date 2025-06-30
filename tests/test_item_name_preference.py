from utils import inventory_processor as ip
from utils import schema_cache as sc


def fake_get_item(defindex: int):
    return {"defindex": defindex, "base_name": "Wrong", "image_url": "i"}


def test_enrich_inventory_prefers_items_game(monkeypatch):
    monkeypatch.setattr(
        sc,
        "get_item",
        lambda idx: {"defindex": idx, "base_name": "Wrong", "image_url": "i"},
    )
    monkeypatch.setattr(ip, "WARPAINT_MAP", {"111": "Correct"})
    data = {"items": [{"defindex": 111, "quality": 6}]}
    items = ip.enrich_inventory(data)
    assert items[0]["name"].endswith("Correct")
