import json

import pytest

import scripts.fetch_data as fd


class DummyResp:
    def __init__(self, payload):
        self.payload = payload
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        if isinstance(self.payload, dict):
            return self.payload
        raise ValueError

    @property
    def text(self):
        if isinstance(self.payload, str):
            return self.payload
        return json.dumps(self.payload)


def fake_get(url, timeout=30):
    if "GetSchemaItems" in url:
        return DummyResp({"result": {"items": []}})
    if "GetSchemaOverview" in url:
        return DummyResp({"result": {"qualities": {"0": "Normal"}}})
    if "items_game.txt" in url:
        return DummyResp("items_game\n{")
    if "inventory" in url:
        return DummyResp({"success": True})
    raise AssertionError(f"Unexpected url {url}")


@pytest.fixture(autouse=True)
def patch_requests(monkeypatch):
    monkeypatch.setattr(fd, "requests", type("R", (), {"get": fake_get}))


def test_fetch_all(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fd.fetch_all(api_key="k", steamid="1")
    assert (tmp_path / "cache/schema_items.json").exists()
    assert (tmp_path / "cache/schema_overview.json").exists()
    assert (tmp_path / "cache/items_game.txt").exists()
    assert (tmp_path / "cache/inventory_1.json").exists()
