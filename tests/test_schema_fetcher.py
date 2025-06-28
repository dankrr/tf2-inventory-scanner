# ruff: noqa: E402
import os
import json

from unittest.mock import Mock

os.environ.setdefault("BACKPACK_API_KEY", "x")

import time

import utils.schema_fetcher as sf


def test_schema_cache_hit(tmp_path, monkeypatch):
    cache = tmp_path / "item_schema.json"
    sample = {
        "fetched": time.time(),
        "items": {
            "1;0;1": {
                "defindex": 1,
                "name": "Item",
                "image_url": "i",
                "quality": 0,
                "craftable": True,
            }
        },
    }
    cache.write_text(json.dumps(sample))
    monkeypatch.setattr(sf, "CACHE_FILE", cache)
    monkeypatch.setattr(sf, "requests", Mock())
    schema = sf.ensure_schema_cached()
    assert schema == sample["items"]


def test_schema_cache_miss(tmp_path, monkeypatch):
    cache = tmp_path / "item_schema.json"
    monkeypatch.setattr(sf, "CACHE_FILE", cache)

    class DummyResp:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self.payload

    payload = {
        "items": [
            {
                "defindex": 2,
                "name": "Other",
                "image_url": "u",
                "quality": 0,
                "craftable": True,
            }
        ]
    }

    def fake_get(url, timeout):
        assert url == sf.SCHEMA_URL
        return DummyResp(payload)

    monkeypatch.setattr(sf.requests, "get", fake_get)
    schema = sf.ensure_schema_cached()
    assert schema == {
        "2;0;1": {
            "defindex": 2,
            "name": "Other",
            "image_url": "u",
            "quality": 0,
            "craftable": True,
        }
    }
    assert cache.exists()
