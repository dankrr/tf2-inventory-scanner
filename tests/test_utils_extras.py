import asyncio
from utils import steam_api_client as sac
from utils import inventory_processor as ip
from utils import local_data as ld
import pytest


def test_convert_to_steam64():
    assert asyncio.run(sac.convert_to_steam64("STEAM_0:1:4")) == "76561197960265737"
    assert asyncio.run(sac.convert_to_steam64("[U:1:4]")) == "76561197960265732"


@pytest.fixture(autouse=True)
def reset_data():
    ld.ITEMS_BY_DEFINDEX = {}


def test_process_inventory_sorting():
    data = {"items": [{"defindex": 2}, {"defindex": 1}]}
    ld.ITEMS_BY_DEFINDEX = {
        1: {"item_name": "A", "image_url": "b"},
        2: {"item_name": "B", "image_url": "a"},
    }
    ld.QUALITIES_BY_INDEX = {}
    items = ip.process_inventory(data)
    assert [item["name"] for item in items] == ["A", "B"]
