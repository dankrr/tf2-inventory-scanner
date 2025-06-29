import json

from unittest.mock import Mock

import utils.schema_fetcher as sf


def test_schema_cache_hit(tmp_path, monkeypatch):
    cache = tmp_path / "tf2_schema.json"
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
    cache = tmp_path / "tf2_schema.json"
    monkeypatch.setattr(sf, "CACHE_FILE", cache)

    class DummyResp:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self.payload

    responses = [
        {"result": {"qualities": {"Normal": 0}}},
        {
            "result": {
                "items": [
                    {
                        "defindex": 2,
                        "name": "Other",
                        "image_url": "u",
                        "image_url_large": None,
                    }
                ]
            }
        },
    ]
    captured = []

    def fake_get(url, timeout):
        captured.append(url)
        return DummyResp(responses.pop(0))

    monkeypatch.setattr(sf.requests, "get", fake_get)
    schema = sf.ensure_schema_cached(api_key="k")
    assert schema == {
        "2": {
            "defindex": 2,
            "name": "Other",
            "image_url": "https://steamcommunity-a.akamaihd.net/economy/image/u/360fx360f",
        }
    }
    assert cache.exists()
    assert any("GetSchemaOverview" in u for u in captured)
    assert any("GetSchemaItems" in u for u in captured)
