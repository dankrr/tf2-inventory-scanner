from utils.price_service import format_price

currencies = {"keys": {"price": {"value_raw": 67.16}}}


def test_format_price_metal_to_keys_and_ref():
    assert format_price(123.44, currencies) == "1 Key 56.28 Refined"


def test_format_price_exact_key():
    assert format_price(67.16, currencies) == "1 Key"


def test_format_price_keys_currency():
    assert format_price(134.32, currencies) == "2 Keys"


def test_format_price_custom_exact_key():
    assert format_price(67.16, currencies) == "1 Key"


def test_format_price_custom_keys_and_refined():
    assert format_price(123.44, currencies) == "1 Key 56.28 Refined"
