import json

from unittest.mock import Mock

import utils.schema_fetcher as sf


def test_schema_cache_hit(tmp_path, monkeypatch):
    cache = tmp_path / "item_schema.json"
    sample = {"1": {"defindex": 1, "name": "Item"}}
    cache.write_text(json.dumps(sample))
    monkeypatch.setattr(sf, "CACHE_FILE", cache)
    monkeypatch.setattr(sf, "requests", Mock())
    schema = sf.ensure_schema_cached(api_key="k")
    assert schema == sample


def test_schema_cache_miss(tmp_path, monkeypatch):
    cache = tmp_path / "item_schema.json"
    monkeypatch.setattr(sf, "CACHE_FILE", cache)

    class DummyResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"result": {"items": [{"defindex": 2, "name": "Other"}]}}

    monkeypatch.setattr(sf.requests, "get", lambda url, timeout: DummyResp())
    schema = sf.ensure_schema_cached(api_key="k")
    assert schema == {"2": {"defindex": 2, "name": "Other"}}
    assert cache.exists()
