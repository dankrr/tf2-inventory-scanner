from utils import steam_api_client as sac
from utils import inventory_processor as ip
from utils import schema_fetcher as sf
from utils import items_game_cache as ig
import pytest


def test_convert_to_steam64():
    assert sac.convert_to_steam64("STEAM_0:1:4") == "76561197960265737"
    assert sac.convert_to_steam64("[U:1:4]") == "76561197960265732"


@pytest.fixture(autouse=True)
def no_items_game(monkeypatch):
    monkeypatch.setattr(ig, "ensure_items_game_cached", lambda: {})
    monkeypatch.setattr(ig, "ITEM_BY_DEFINDEX", {}, False)
    from utils import local_data as ld

    ld.TF2_SCHEMA = {}


def test_process_inventory_sorting():
    data = {"items": [{"defindex": 2}, {"defindex": 1}]}
    sf.SCHEMA = {
        "1": {"defindex": 1, "item_name": "A", "image_url": "b"},
        "2": {"defindex": 2, "item_name": "B", "image_url": "a"},
    }
    sf.QUALITIES = {}
    items = ip.process_inventory(data)
    assert [item["name"] for item in items] == ["A", "B"]
