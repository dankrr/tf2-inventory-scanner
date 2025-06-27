from utils import steam_api_client as sac
from utils import inventory_processor as ip
from utils import schema_fetcher as sf


def test_convert_to_steam64():
    assert sac.convert_to_steam64("STEAM_0:1:4") == "76561197960265737"
    assert sac.convert_to_steam64("[U:1:4]") == "76561197960265732"


def test_process_inventory_sorting():
    data = {
        "assets": [{"classid": "1"}, {"classid": "2"}],
        "descriptions": [
            {"classid": "1", "icon_url": "a", "app_data": {"def_index": "2"}},
            {"classid": "2", "icon_url": "b", "app_data": {"def_index": "1"}},
        ],
    }
    sf.SCHEMA = {
        "1": {"defindex": 1, "name": "B", "image_url": "a"},
        "2": {"defindex": 2, "name": "A", "image_url": "b"},
    }
    sf.QUALITIES = {}
    items = ip.process_inventory(data)
    assert [item["name"] for item in items] == ["A", "B"]
