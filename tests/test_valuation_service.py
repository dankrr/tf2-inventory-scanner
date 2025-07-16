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


def test_crate_case_prices(monkeypatch):
    price_map = {
        (
            "Summer 2024 Cosmetic Case",
            6,
            True,
            False,
            0,
            0,
        ): {"value_raw": 0.22, "currency": "metal"},
        (
            "Mann Co. Supply Crate",
            6,
            True,
            False,
            0,
            0,
        ): {"value_raw": 0.33, "currency": "metal"},
        (
            "Summer 2024 Cosmetic Case",
            6,
            False,
            False,
            0,
            0,
        ): {"value_raw": 0.22, "currency": "metal"},
        (
            "Mann Co. Supply Crate",
            6,
            False,
            False,
            0,
            0,
        ): {"value_raw": 0.33, "currency": "metal"},
    }
    local_data.ITEMS_BY_DEFINDEX = {
        5959: {"item_name": "Summer 2024 Cosmetic Case"},
        5022: {"item_name": "Mann Co. Supply Crate"},
    }
    local_data.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}
    service = ValuationService(price_map=price_map)

    assert service.get_price(defindex=5959) == "0.22 ref"
    assert service.get_price(name="Summer 2024 Cosmetic Case") == "0.22 ref"
    assert service.get_price(defindex=5959, craftable=False) == "0.22 ref"
    assert (
        service.get_price(name="Summer 2024 Cosmetic Case", craftable=False)
        == "0.22 ref"
    )
    assert service.get_price(defindex=5022, craftable=False) == "0.33 ref"
