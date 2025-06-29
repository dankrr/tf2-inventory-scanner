import json

from unittest.mock import Mock

import utils.schema_fetcher as sf


def test_schema_cache_hit(tmp_path, monkeypatch):
    cache = tmp_path / "tf2schema.json"
    sample = {
        "items": {
            str(i): {
                "defindex": i,
                "name": "Item",
                "image_url": "https://steamcommunity-a.akamaihd.net/economy/image/i/360fx360f",
            }
            for i in range(5000)
        },
        "qualities": {"0": "Normal"},
    }
    cache.write_text(json.dumps(sample))
    monkeypatch.setattr(sf, "CACHE_FILE", cache)
    monkeypatch.setattr(sf, "requests", Mock())
    schema = sf.ensure_schema_cached(api_key="k")
    assert schema == sample["items"]


def test_schema_cache_miss(tmp_path, monkeypatch):
    cache = tmp_path / "tf2schema.json"
    monkeypatch.setattr(sf, "CACHE_FILE", cache)

    class DummyResp:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self.payload

    payload = {
        "items": {
            "2": {
                "defindex": 2,
                "name": "Other",
                "image_url": "u",
            }
        },
        "qualities": {"0": "Normal"},
    }
    captured = []

    def fake_get(url, timeout):
        captured.append(url)
        return DummyResp(payload)

    monkeypatch.setattr(sf.requests, "get", fake_get)
    schema = sf.ensure_schema_cached(api_key="k")
    assert schema == payload["items"]
    assert cache.exists()
    assert any("/schema" in u for u in captured)
