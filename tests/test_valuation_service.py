from utils.valuation_service import ValuationService
from utils import local_data


def test_get_price_info():
    price_map = {
        (
            "Item",
            6,
            True,
            False,
            0,
            0,
        ): {"value_raw": 5.0, "currency": "metal"}
    }
    service = ValuationService(price_map=price_map)
    assert service.get_price_info("Item", 6, True) == {
        "value_raw": 5.0,
        "currency": "metal",
    }


def test_format_price(monkeypatch):
    price_map = {
        (
            "Item",
            6,
            True,
            False,
            0,
            0,
        ): {"value_raw": 50.0, "currency": "metal"}
    }
    service = ValuationService(price_map=price_map)
    local_data.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}
    assert service.format_price("Item", 6, True) == "1 Key"


def test_killstreak_tier_lookup(monkeypatch):
    price_map = {
        (
            "Item",
            6,
            True,
            False,
            0,
            2,
        ): {"value_raw": 100.0, "currency": "keys"}
    }
    service = ValuationService(price_map=price_map)
    local_data.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}
    assert service.format_price("Item", 6, True, killstreak_tier=2) == "2 Keys"
