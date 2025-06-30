import json
from unittest.mock import Mock

import utils.tf2_schema_fetcher as tsf


def test_tf2_schema_cache_hit(tmp_path, monkeypatch):
    cache = tmp_path / "tf2_schema.json"
    sample = {"items": {"1": {"name": "One"}}}
    cache.write_text(json.dumps(sample))
    monkeypatch.setattr(tsf, "CACHE_PATH", cache)
    monkeypatch.setattr(tsf, "requests", Mock())
    data = tsf.ensure_schema_cached()
    assert data == sample


def test_tf2_schema_cache_miss(tmp_path, monkeypatch):
    cache = tmp_path / "tf2_schema.json"
    monkeypatch.setattr(tsf, "CACHE_PATH", cache)

    class DummyResp:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self.payload

    response = {"items": {"2": {"name": "Two"}}}

    def fake_get(url, timeout):
        assert url.endswith("/schema")
        return DummyResp(response)

    monkeypatch.setattr(tsf.requests, "get", fake_get)
    data = tsf.ensure_schema_cached()
    assert data == response
    assert cache.exists()
