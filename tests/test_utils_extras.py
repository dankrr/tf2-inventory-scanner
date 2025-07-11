from utils import steam_api_client as sac
from utils import inventory_processor as ip
from utils import local_data as ld
from utils.valuation_service import ValuationService
import pytest


def test_convert_to_steam64():
    assert sac.convert_to_steam64("STEAM_0:1:4") == "76561197960265737"
    assert sac.convert_to_steam64("[U:1:4]") == "76561197960265732"


@pytest.fixture(autouse=True)
def reset_data():
    ld.ITEMS_BY_DEFINDEX = {}


def test_process_inventory_sorting():
    data = {"items": [{"defindex": 2, "quality": 6}, {"defindex": 1, "quality": 6}]}
    ld.ITEMS_BY_DEFINDEX = {
        1: {"item_name": "A", "image_url": "b"},
        2: {"item_name": "B", "image_url": "a"},
    }
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {
        ("A", 6, False, 0, 0): {"value_raw": 1.0, "currency": "metal"},
        ("B", 6, False, 0, 0): {"value_raw": 1.0, "currency": "metal"},
    }
    service = ValuationService(price_map=price_map)
    items = ip.process_inventory(data, valuation_service=service)
    assert [item["name"] for item in items] == ["A", "B"]


def test_process_inventory_sorts_by_price():
    data = {"items": [{"defindex": 1, "quality": 6}, {"defindex": 2, "quality": 6}]}
    ld.ITEMS_BY_DEFINDEX = {
        1: {"item_name": "A", "image_url": ""},
        2: {"item_name": "B", "image_url": ""},
    }
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {
        ("A", 6, False, 0, 0): {"value_raw": 2.0, "currency": "metal"},
        ("B", 6, False, 0, 0): {"value_raw": 5.0, "currency": "metal"},
    }
    service = ValuationService(price_map=price_map)
    items = ip.process_inventory(data, valuation_service=service)
    assert [item["name"] for item in items] == ["B", "A"]


@pytest.mark.asyncio
async def test_build_user_data_items_sorted(monkeypatch, app):
    import importlib

    mod = importlib.import_module("app")

    async def fake_summary(_id):
        return {"username": "Test", "avatar": "", "playtime": 0, "profile": ""}

    raw_result = {
        "status": 1,
        "items": [
            {"defindex": 1, "quality": 6},
            {"defindex": 2, "quality": 6},
        ],
    }

    async def fake_fetch(_id):
        return "parsed", raw_result

    monkeypatch.setattr(mod, "get_player_summary", fake_summary)
    monkeypatch.setattr(mod.sac, "fetch_inventory_async", fake_fetch)

    ld.ITEMS_BY_DEFINDEX = {
        1: {"item_name": "A", "image_url": ""},
        2: {"item_name": "B", "image_url": ""},
    }
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {
        ("A", 6, False, 0, 0): {"value_raw": 1.0, "currency": "metal"},
        ("B", 6, False, 0, 0): {"value_raw": 5.0, "currency": "metal"},
    }
    service = ValuationService(price_map=price_map)
    monkeypatch.setattr(mod.ip, "get_valuation_service", lambda: service)

    result = await mod.build_user_data_async("1")
    assert [item["name"] for item in result["items"]] == ["B", "A"]
