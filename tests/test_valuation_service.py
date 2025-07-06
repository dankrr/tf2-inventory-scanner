from utils.valuation_service import ValuationService
from utils import local_data


def test_get_price_info():
    price_map = {("Item", 6, False): {"value_raw": 5.0, "currency": "metal"}}
    service = ValuationService(price_map=price_map)
    assert service.get_price_info("Item", 6) == {"value_raw": 5.0, "currency": "metal"}


def test_format_price(monkeypatch):
    price_map = {("Item", 6, False): {"value_raw": 50.0, "currency": "metal"}}
    service = ValuationService(price_map=price_map)
    local_data.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}
    assert service.format_price("Item", 6) == "1 Key"
