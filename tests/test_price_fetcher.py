import utils.price_fetcher as pf


def test_price_cache_fetch(tmp_path, monkeypatch):
    price_file = tmp_path / "price_cache.json"
    curr_file = tmp_path / "currency_rates.json"
    monkeypatch.setattr(pf, "PRICE_CACHE_FILE", price_file)
    monkeypatch.setattr(pf, "CURRENCY_FILE", curr_file)

    class DummyResp:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self.payload

    prices_payload = {
        "response": {
            "success": 1,
            "items": {
                "30035;6": {
                    "defindex": 30035,
                    "quality": 6,
                    "value": 5100,
                    "currency": "metal",
                    "last_update": 1,
                }
            },
        }
    }
    currencies_payload = {
        "response": {"currencies": {"metal": {"value": 100}, "keys": {"value": 5100}}}
    }

    def fake_get(url, timeout):
        if "IGetPrices" in url:
            return DummyResp(prices_payload)
        return DummyResp(currencies_payload)

    monkeypatch.setattr(pf.requests, "get", fake_get)
    monkeypatch.setenv("BACKPACK_API_KEY", "x")

    prices = pf.ensure_price_cache()
    rate = pf.ensure_currency_rates()

    assert prices["30035;6"]["value"] == 5100
    assert rate == 51.0
    assert price_file.exists()
    assert curr_file.exists()


def test_format_price():
    result = pf.format_price(5150, 5100)
    assert "key" in result and "0.50" in result
