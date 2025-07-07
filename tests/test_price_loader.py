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
    key = ("Mann Co. Supply Crate Key", 6, False, 0, 0)
    assert key in mapping
    assert mapping[key]["currency"] == "metal"


def test_price_map_non_craftable(tmp_path, monkeypatch):
    monkeypatch.setenv("BPTF_API_KEY", "TEST")
    monkeypatch.setattr(price_loader, "PRICES_FILE", tmp_path / "prices.json")
    url = "https://backpack.tf/api/IGetPrices/v4?raw=1&key=TEST"
    payload = {
        "response": {
            "success": 1,
            "items": {
                "Unusual Hat": {
                    "defindex": [123],
                    "prices": {
                        "5": {
                            "Tradable": {
                                "Non-Craftable": [
                                    {
                                        "value": 1,
                                        "value_raw": 1.0,
                                        "currency": "keys",
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
    key = ("Hat", 5, False, 0, 0)
    assert key in mapping
    assert mapping[key]["currency"] == "keys"


def test_price_map_unusual_effect(tmp_path, monkeypatch):
    monkeypatch.setenv("BPTF_API_KEY", "TEST")
    monkeypatch.setattr(price_loader, "PRICES_FILE", tmp_path / "prices.json")
    url = "https://backpack.tf/api/IGetPrices/v4?raw=1&key=TEST"
    payload = {
        "response": {
            "success": 1,
            "items": {
                "Villain's Veil": {
                    "defindex": [30998],
                    "prices": {
                        "5": {
                            "Tradable": {
                                "Craftable": {
                                    "13": {
                                        "value": 2150,
                                        "value_raw": 164554.25,
                                        "currency": "keys",
                                        "last_update": 0,
                                    }
                                }
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
    key = ("Villain's Veil", 5, False, 13, 0)
    assert key in mapping
    assert mapping[key]["currency"] == "keys"


def test_price_map_australium(tmp_path, monkeypatch):
    monkeypatch.setenv("BPTF_API_KEY", "TEST")
    monkeypatch.setattr(price_loader, "PRICES_FILE", tmp_path / "prices.json")
    url = "https://backpack.tf/api/IGetPrices/v4?raw=1&key=TEST"
    payload = {
        "response": {
            "success": 1,
            "items": {
                "Rocket Launcher": {
                    "defindex": [205],
                    "australium": "1",
                    "prices": {
                        "6": {
                            "Tradable": {
                                "Craftable": [
                                    {
                                        "value": 100,
                                        "value_raw": 100.0,
                                        "currency": "keys",
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
    assert ("Rocket Launcher", 6, True, 0, 0) in mapping


def test_price_map_killstreak(tmp_path, monkeypatch):
    monkeypatch.setenv("BPTF_API_KEY", "TEST")
    monkeypatch.setattr(price_loader, "PRICES_FILE", tmp_path / "prices.json")
    url = "https://backpack.tf/api/IGetPrices/v4?raw=1&key=TEST"
    payload = {
        "response": {
            "success": 1,
            "items": {
                "Professional Killstreak Rocket Launcher": {
                    "defindex": [205],
                    "prices": {
                        "6": {
                            "Tradable": {
                                "Craftable": [
                                    {
                                        "value": 100,
                                        "value_raw": 100.0,
                                        "currency": "keys",
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
    assert ("Rocket Launcher", 6, False, 0, 3) in mapping


def test_price_map_quality_killstreak(tmp_path, monkeypatch):
    monkeypatch.setenv("BPTF_API_KEY", "TEST")
    monkeypatch.setattr(price_loader, "PRICES_FILE", tmp_path / "prices.json")
    url = "https://backpack.tf/api/IGetPrices/v4?raw=1&key=TEST"
    payload = {
        "response": {
            "success": 1,
            "items": {
                "Strange Professional Killstreak Rocket Launcher": {
                    "defindex": [205],
                    "prices": {
                        "11": {
                            "Tradable": {
                                "Craftable": [
                                    {
                                        "value": 100,
                                        "value_raw": 100.0,
                                        "currency": "keys",
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
    assert ("Rocket Launcher", 11, False, 0, 3) in mapping


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("BPTF_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        price_loader.ensure_prices_cached(refresh=True)
