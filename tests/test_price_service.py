from utils.price_service import convert_price_to_keys_ref, convert_to_key_ref


def test_convert_price_to_keys_ref_basic():
    currencies = {"keys": {"price": {"value_raw": 50.0}}}
    out = convert_price_to_keys_ref(25.0, "metal", currencies)
    assert out == "25.0 Refined"


def test_convert_price_to_keys_ref_keys():
    currencies = {"keys": {"price": {"value_raw": 50.0}}}
    out = convert_price_to_keys_ref(1.5, "keys", currencies)
    assert out == "1.5 Keys"


def test_convert_to_key_ref_only_refined():
    assert convert_to_key_ref(5.0) == "5.00 Refined"


def test_convert_to_key_ref_keys_and_refined():
    assert convert_to_key_ref(125.5) == "2 Keys 25.50 Refined"
