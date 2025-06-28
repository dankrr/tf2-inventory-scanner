# ruff: noqa: E402
import os
import json

from unittest.mock import Mock

os.environ.setdefault("BACKPACK_API_KEY", "x")

import utils.schema_fetcher as sf


def test_schema_cache_hit(tmp_path, monkeypatch):
    cache = tmp_path / "item_schema.json"
    sample = {
        "items": {"1": {"defindex": 1, "name": "Item", "image_url": "i"}},
        "qualities": {"0": "Normal"},
    }
    cache.write_text(json.dumps(sample))
    monkeypatch.setattr(sf, "CACHE_FILE", cache)
    monkeypatch.setattr(sf, "requests", Mock())
    schema = sf.ensure_schema_cached(api_key="k")
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
            "image_url": "u",
            "image_url_large": None,
        }
    }
    assert cache.exists()
    assert any("GetSchemaOverview" in u for u in captured)
    assert any("GetSchemaItems" in u for u in captured)
