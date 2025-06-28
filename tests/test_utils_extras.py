# ruff: noqa: E402
import os

os.environ.setdefault("BACKPACK_API_KEY", "x")

from utils import steam_api_client as sac
from utils import inventory_processor as ip
from utils import schema_fetcher as sf


def test_convert_to_steam64():
    assert sac.convert_to_steam64("STEAM_0:1:4") == "76561197960265737"
    assert sac.convert_to_steam64("[U:1:4]") == "76561197960265732"


def test_process_inventory_sorting():
    data = {"items": [{"defindex": 2}, {"defindex": 1}]}
    sf.SCHEMA = {
        "1": {"defindex": 1, "item_name": "A", "image_url": "b"},
        "2": {"defindex": 2, "item_name": "B", "image_url": "a"},
    }
    sf.QUALITIES = {}
    items = ip.process_inventory(data)
    assert [item["name"] for item in items] == ["A", "B"]
