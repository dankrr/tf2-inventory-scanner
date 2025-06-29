import json

import utils.items_game_cache as ig


def test_items_game_cache_hit(tmp_path, monkeypatch):
    json_file = tmp_path / "items_game.json"
    sample = {"items": {"1": {"name": "One"}}}
    json_file.write_text(json.dumps(sample))
    monkeypatch.setattr(ig, "JSON_FILE", json_file)
    ig.ITEMS_GAME = None
    data = ig.ensure_items_game_cached()
    assert data == sample


class DummyResp:
    def __init__(self, payload=None):
        self.payload = payload or {"items": {"1": {"name": "One"}}}

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_items_game_cache_miss(tmp_path, monkeypatch):
    monkeypatch.setattr(ig, "JSON_FILE", tmp_path / "items_game.json")
    monkeypatch.setattr(ig.requests, "get", lambda url, timeout: DummyResp())
    ig.ITEMS_GAME = None
    data = ig.ensure_items_game_cached()
    assert data.get("items", {}).get("1", {}).get("name") == "One"
    assert ig.JSON_FILE.exists()
