import json

import utils.items_game_cache as ig


def test_items_game_cache_hit(tmp_path, monkeypatch):
    json_file = tmp_path / "items_game.json"
    sample = {"items": {"1": {"name": "One"}}}
    json_file.write_text(json.dumps(sample))
    monkeypatch.setattr(ig, "JSON_FILE", json_file)
    monkeypatch.setattr(ig, "RAW_FILE", tmp_path / "items_game_raw.txt")
    ig.ITEMS_GAME = None
    data = ig.ensure_items_game_cached()
    assert data == sample


class DummyResp:
    def __init__(
        self,
        text='"items_game"\n{\n "items"\n {\n  "1"\n  {\n   "name" "One"\n  }\n }\n}\n',
    ):
        self.text = text

    def raise_for_status(self):
        pass


def test_items_game_cache_miss(tmp_path, monkeypatch):
    monkeypatch.setattr(ig, "JSON_FILE", tmp_path / "items_game.json")
    monkeypatch.setattr(ig, "RAW_FILE", tmp_path / "items_game_raw.txt")
    monkeypatch.setattr(ig.requests, "get", lambda url, timeout: DummyResp())
    ig.ITEMS_GAME = None
    data = ig.ensure_items_game_cached()
    assert data.get("items", {}).get("1", {}).get("name") == "One"
    assert ig.JSON_FILE.exists()
