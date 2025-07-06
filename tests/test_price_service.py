from utils.price_service import convert_price_to_keys_ref


def test_convert_price_to_keys_ref_basic():
    currencies = {"metal": {"value_raw": 1.0}, "keys": {"value_raw": 50.0}}
    out = convert_price_to_keys_ref(25.0, "metal", currencies)
    assert out == "25 Refined"


def test_convert_price_to_keys_ref_keys():
    currencies = {"metal": {"value_raw": 1.0}, "keys": {"value_raw": 50.0}}
    out = convert_price_to_keys_ref(1.5, "keys", currencies)
    assert out == "1 Key 25 Refined"
