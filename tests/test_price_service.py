from utils.price_service import format_price


def test_format_price_basic():
    currencies = {"keys": {"price": {"value_raw": 50.0}}}
    assert format_price(25.0, currencies) == "25.00 ref"


def test_format_price_keys_only():
    currencies = {"keys": {"price": {"value_raw": 50.0}}}
    assert format_price(100.0, currencies) == "2 Keys"


def test_format_price_keys_and_ref():
    currencies = {"keys": {"price": {"value_raw": 50.0}}}
    assert format_price(125.5, currencies) == "2 Keys 25.50 ref"


def test_format_price_only_refined():
    currencies = {"keys": {"price": {"value_raw": 50.0}}}
    assert format_price(5.0, currencies) == "5.00 ref"


def test_format_price_example():
    currencies = {"keys": {"price": {"value_raw": 67.165}}}
    val = 164554.25
    assert format_price(val, currencies) == "2449 Keys 67.16 ref"
