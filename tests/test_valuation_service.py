from utils.valuation_service import ValuationService
from utils import local_data
from utils import price_loader
from utils import valuation_service as vs
import os
import time


def test_get_price_info():
    price_map = {
        (
            "Item",
            6,
            True,
            False,
            0,
            0,
        ): {"value_raw": 5.0, "currency": "metal"}
    }
    service = ValuationService(price_map=price_map)
    assert service.get_price_info("Item", 6, True) == {
        "value_raw": 5.0,
        "currency": "metal",
    }


def test_format_price(monkeypatch):
    price_map = {
        (
            "Item",
            6,
            True,
            False,
            0,
            0,
        ): {"value_raw": 50.0, "currency": "metal"}
    }
    service = ValuationService(price_map=price_map)
    local_data.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}
    assert service.format_price("Item", 6, True) == "1 Key"


def test_killstreak_tier_lookup(monkeypatch):
    price_map = {
        (
            "Item",
            6,
            True,
            False,
            0,
            2,
        ): {"value_raw": 100.0, "currency": "keys"}
    }
    service = ValuationService(price_map=price_map)
    local_data.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}
    assert service.format_price("Item", 6, True, killstreak_tier=2) == "2 Keys"


def test_cached_map_used_when_up_to_date(tmp_path, monkeypatch):
    price_file = tmp_path / "prices.json"
    price_file.write_text("{}")
    map_file = tmp_path / "map.json"
    price_loader.dump_price_map({"cached": True}, map_file)
    now = time.time()
    os.utime(price_file, (now, now))
    os.utime(map_file, (now + 5, now + 5))
    monkeypatch.setattr(price_loader, "PRICES_FILE", price_file)
    monkeypatch.setattr(price_loader, "PRICE_MAP_FILE", map_file)
    monkeypatch.setattr(vs, "PRICE_MAP_FILE", map_file)
    monkeypatch.setattr(
        price_loader, "ensure_prices_cached", lambda refresh=False: price_file
    )
    monkeypatch.setattr(vs, "ensure_prices_cached", lambda refresh=False: price_file)
    monkeypatch.setattr(
        price_loader, "dump_price_map", lambda mapping, path=map_file: path
    )
    monkeypatch.setattr(vs, "dump_price_map", lambda mapping, path=map_file: path)
    called = {"build": False}

    def fake_build(path):
        called["build"] = True
        return {"built": True}

    monkeypatch.setattr(price_loader, "build_price_map", fake_build)
    monkeypatch.setattr(vs, "build_price_map", fake_build)
    monkeypatch.setattr(price_loader, "load_price_map", lambda path: {"cached": True})
    monkeypatch.setattr(vs, "load_price_map", lambda path: {"cached": True})

    service = ValuationService()
    assert called["build"] is False
    assert service.price_map == {"cached": True}


def test_price_map_rebuilt_if_prices_newer(tmp_path, monkeypatch):
    price_file = tmp_path / "prices.json"
    price_file.write_text("{}")
    map_file = tmp_path / "map.json"
    price_loader.dump_price_map({"cached": True}, map_file)
    now = time.time()
    os.utime(map_file, (now, now))
    os.utime(price_file, (now + 10, now + 10))
    monkeypatch.setattr(price_loader, "PRICES_FILE", price_file)
    monkeypatch.setattr(price_loader, "PRICE_MAP_FILE", map_file)
    monkeypatch.setattr(vs, "PRICE_MAP_FILE", map_file)
    monkeypatch.setattr(
        price_loader, "ensure_prices_cached", lambda refresh=False: price_file
    )
    monkeypatch.setattr(vs, "ensure_prices_cached", lambda refresh=False: price_file)
    monkeypatch.setattr(
        price_loader, "dump_price_map", lambda mapping, path=map_file: path
    )
    monkeypatch.setattr(vs, "dump_price_map", lambda mapping, path=map_file: path)
    called = {"build": False}

    def fake_build(path):
        called["build"] = True
        return {"built": True}

    monkeypatch.setattr(price_loader, "build_price_map", fake_build)
    monkeypatch.setattr(vs, "build_price_map", fake_build)

    def fail_load(path):
        raise AssertionError("load should not be called")

    monkeypatch.setattr(price_loader, "load_price_map", fail_load)
    monkeypatch.setattr(vs, "load_price_map", fail_load)

    service = ValuationService()
    assert called["build"] is True
    assert service.price_map == {"built": True}
