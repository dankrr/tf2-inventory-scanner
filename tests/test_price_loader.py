import responses
import pytest

from utils import price_loader


def test_price_map_smoke(tmp_path, monkeypatch):
    monkeypatch.setenv("BPTF_API_KEY", "TEST")
    monkeypatch.setattr(price_loader, "PRICES_FILE", tmp_path / "prices.json")
    url = "https://backpack.tf/api/IGetPrices/v4?raw=1&key=TEST"
    payload = {
        "response": {
            "success": 1,
            "items": {
                "Mann Co. Supply Crate Key": {
                    "defindex": [5021],
                    "prices": {
                        "6": {
                            "Tradable": {
                                "Craftable": [
                                    {
                                        "value": 57,
                                        "value_raw": 57.0,
                                        "currency": "metal",
                                        "last_update": 0,
                                    }
                                ]
                            }
                        }
                    },
                }
            },
        }
    }

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, url, json=payload, status=200)
        p = price_loader.ensure_prices_cached(refresh=True)

    mapping = price_loader.build_price_map(p)
    assert (5021, 6) in mapping
    assert mapping[(5021, 6)]["currency"] == "metal"


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("BPTF_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        price_loader.ensure_prices_cached(refresh=True)
