# ruff: noqa: E402
import os
import json

from unittest.mock import Mock

os.environ.setdefault("BACKPACK_API_KEY", "x")

import utils.schema_fetcher as sf


def test_schema_cache_hit(tmp_path, monkeypatch):
    cache = tmp_path / "cached_schema.json"
    sample = {
        "items": [
            {
                "defindex": 1,
                "name": "Item",
                "image_url": "i",
                "quality": 0,
                "craftable": True,
            }
        ]
    }
    cache.write_text(json.dumps(sample))
    monkeypatch.setattr(sf, "CACHE_FILE", cache)
    monkeypatch.setattr(sf, "requests", Mock())
    schema = sf.ensure_schema_cached()
    assert schema == {"1;0;1": sample["items"][0]}


def test_schema_cache_miss(tmp_path, monkeypatch):
    cache = tmp_path / "cached_schema.json"
    monkeypatch.setattr(sf, "CACHE_FILE", cache)

    class DummyResp:
        def __init__(self, payload):
            self.content = json.dumps(payload).encode()

        def raise_for_status(self):
            pass

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

    def fake_get(url, stream=False, timeout=20):
        assert url == sf.SCHEMA_URL
        assert stream is True
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


def test_resolve_item_names_bulk(monkeypatch):
    captured = {}

    def fake_post(url, headers=None, json=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers

        class DummyResp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"itemNames": ["Item"]}

        return DummyResp()

    monkeypatch.setattr(sf.requests, "post", fake_post)
    names = sf.resolve_item_names_bulk([{"defindex": 1, "quality": 6}])
    assert names == ["Item"]
    assert captured["url"] == sf.BULK_NAME_URL
