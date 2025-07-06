import utils.price_service as ps

currencies = {"keys": {"price": {"value_raw": 67.16}}}


def test_convert_metal_to_keys_and_ref():
    out = ps.convert_price_to_keys_ref(123.44, "metal", currencies)
    assert out == "1 Keys 56.28 Refined"


def test_convert_exact_key_price():
    out = ps.convert_price_to_keys_ref(67.16, "metal", currencies)
    assert out == "1 Keys"


def test_convert_keys_currency():
    out = ps.convert_price_to_keys_ref(2, "keys", currencies)
    assert out == "2 Keys"
