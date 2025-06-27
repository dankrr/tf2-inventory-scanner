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
    ip.SCHEMA = {
        "1": {"defindex": 1, "name": "One"},
        "2": {"defindex": 2, "name": "Two"},
    }
    items = ip.process_inventory(data)
    assert {i["name"] for i in items} == {"One", "Two"}
    for item in items:
        if item["name"] == "One":
            assert item["image_url"].startswith(
                "https://community.cloudflare.steamstatic.com/economy/image/"
            )
        else:
            assert item["image_url"] == ""
