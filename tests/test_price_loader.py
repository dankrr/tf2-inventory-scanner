import responses
import pytest
import requests

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
    key = ("Mann Co. Supply Crate Key", 6, True, False, 0, 0)
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
    key = ("Hat", 5, False, False, 0, 0)
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
    key = ("Villain's Veil", 5, True, False, 13, 0)
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
    assert ("Rocket Launcher", 6, True, True, 0, 0) in mapping


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
    assert ("Rocket Launcher", 6, True, False, 0, 3) in mapping


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
    assert ("Rocket Launcher", 11, True, False, 0, 3) in mapping


def test_price_map_newline_name(tmp_path, monkeypatch):
    monkeypatch.setenv("BPTF_API_KEY", "TEST")
    monkeypatch.setattr(price_loader, "PRICES_FILE", tmp_path / "prices.json")
    url = "https://backpack.tf/api/IGetPrices/v4?raw=1&key=TEST"
    payload = {
        "response": {
            "success": 1,
            "items": {
                "Cool War Paint\n(Factory New)": {
                    "defindex": [1234],
                    "prices": {
                        "6": {
                            "Tradable": {
                                "Craftable": [
                                    {
                                        "value": 10,
                                        "value_raw": 10.0,
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
    assert ("Cool War Paint (Factory New)", 6, True, False, 0, 0) in mapping


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("BPTF_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        price_loader.ensure_prices_cached(refresh=True)


def test_dump_and_load_price_map(tmp_path):
    mapping = {("A", 6, True, False, 0, 0): {"value_raw": 1, "currency": "metal"}}
    path = tmp_path / "map.json"
    price_loader.dump_price_map(mapping, path)
    loaded = price_loader.load_price_map(path)
    assert loaded == mapping


def test_price_map_dict_entry(tmp_path, monkeypatch):
    monkeypatch.setenv("BPTF_API_KEY", "TEST")
    monkeypatch.setattr(price_loader, "PRICES_FILE", tmp_path / "prices.json")
    url = "https://backpack.tf/api/IGetPrices/v4?raw=1&key=TEST"
    payload = {
        "response": {
            "success": 1,
            "items": {
                "Lugermorph": {
                    "defindex": [160],
                    "prices": {
                        "3": {
                            "Tradable": {
                                "Craftable": {
                                    "0": {
                                        "value": 12.4,
                                        "value_raw": 12.4,
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
    assert ("Lugermorph", 3, True, False, 0, 0) in mapping


def test_timeout_creates_empty_cache(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BPTF_API_KEY", "TEST")
    monkeypatch.setattr(price_loader, "PRICES_FILE", tmp_path / "prices.json")
    monkeypatch.setenv("PRICE_RETRIES", "2")
    monkeypatch.setenv("PRICE_DELAY", "0")

    calls = {"n": 0}

    def fail(*a, **k):
        calls["n"] += 1
        raise requests.Timeout("timeout")

    monkeypatch.setattr(price_loader.requests, "get", fail)
    monkeypatch.setattr(price_loader.time, "sleep", lambda s: None)

    p = price_loader.ensure_prices_cached(refresh=True)
    out = capsys.readouterr().out

    assert calls["n"] == 2
    assert p.exists()
    assert p.read_text() == "{}"
    assert "Could not fetch Backpack.tf prices after 2 attempts" in out


def test_detect_and_delete_incomplete_cache(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BPTF_API_KEY", "TEST")
    path = tmp_path / "prices.json"
    path.write_text("partial")
    monkeypatch.setattr(price_loader, "PRICES_FILE", path)
    monkeypatch.setenv("PRICE_RETRIES", "1")
    monkeypatch.setenv("PRICE_DELAY", "0")

    calls = {"n": 0}

    def fail(*a, **k):
        calls["n"] += 1
        raise requests.Timeout("timeout")

    monkeypatch.setattr(price_loader.requests, "get", fail)
    monkeypatch.setattr(price_loader.time, "sleep", lambda s: None)

    p = price_loader.ensure_prices_cached()
    out = capsys.readouterr().out

    assert calls["n"] == 1
    assert p.exists()
    assert p.read_text() == "{}"
    assert "Detected incomplete price cache" in out


def test_refresh_ignores_incomplete_cache(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BPTF_API_KEY", "TEST")
    path = tmp_path / "prices.json"
    path.write_text("x")
    monkeypatch.setattr(price_loader, "PRICES_FILE", path)
    monkeypatch.setenv("PRICE_RETRIES", "1")
    monkeypatch.setenv("PRICE_DELAY", "0")

    calls = {"n": 0}

    def fail(*a, **k):
        calls["n"] += 1
        raise requests.Timeout("timeout")

    monkeypatch.setattr(price_loader.requests, "get", fail)
    monkeypatch.setattr(price_loader.time, "sleep", lambda s: None)

    p = price_loader.ensure_prices_cached(refresh=True)
    out = capsys.readouterr().out

    assert calls["n"] == 1
    assert p.exists()
    assert p.read_text() == "{}"
    assert "Detected incomplete price cache" in out
