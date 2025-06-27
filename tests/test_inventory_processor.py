from utils import inventory_processor as ip
from utils import schema_fetcher as sf


def test_enrich_inventory():
    data = {
        "assets": [{"classid": "1"}],
        "descriptions": [
            {
                "classid": "1",
                "icon_url": "icon.png",
                "app_data": {"def_index": "111"},
            }
        ],
    }
    sf.SCHEMA = {"111": {"defindex": 111, "name": "Test Item", "image_url": "img"}}
    sf.QUALITIES = {}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Test Item"
    assert items[0]["image_url"].startswith(
        "https://community.cloudflare.steamstatic.com/economy/image/"
    )


def test_process_inventory_handles_missing_icon():
    data = {
        "assets": [{"classid": "1"}, {"classid": "2"}],
        "descriptions": [
            {"classid": "1", "icon_url": "icon.png", "app_data": {"def_index": "1"}},
            {"classid": "2", "app_data": {"def_index": "2"}},
        ],
    }
    sf.SCHEMA = {
        "1": {"defindex": 1, "name": "One", "image_url": "a"},
        "2": {"defindex": 2, "name": "Two", "image_url": ""},
    }
    sf.QUALITIES = {}
    items = ip.process_inventory(data)
    assert {i["name"] for i in items} == {"One", "Two"}
    for item in items:
        if item["name"] == "One":
            assert item["image_url"].startswith(
                "https://community.cloudflare.steamstatic.com/economy/image/"
            )
        else:
            assert item["image_url"] == ""
