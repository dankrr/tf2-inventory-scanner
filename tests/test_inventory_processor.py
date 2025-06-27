from utils import inventory_processor as ip


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
    ip.SCHEMA = {"111": {"defindex": 111, "name": "Test Item"}}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Test Item"
    assert items[0]["image_url"].startswith(
        "https://steamcommunity-a.akamaihd.net/economy/image/"
    )
