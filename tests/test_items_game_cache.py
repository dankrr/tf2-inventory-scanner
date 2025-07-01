import json

import utils.items_game_cache as ig


def test_items_game_cache_hit(tmp_path, monkeypatch):
    json_file = tmp_path / "items_game.json"
    sample = {"items": {"1": {"name": "One"}}}
    json_file.write_text(json.dumps(sample))
    monkeypatch.setattr(ig, "JSON_FILE", json_file)
    monkeypatch.setattr(ig, "RAW_FILE", tmp_path / "items_game.txt")
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
    monkeypatch.setattr(ig, "RAW_FILE", tmp_path / "items_game.txt")
    monkeypatch.setattr(ig.requests, "get", lambda url, timeout: DummyResp())
    ig.ITEMS_GAME = None
    data = ig.ensure_items_game_cached()
    assert data.get("items", {}).get("1", {}).get("name") == "One"
    assert ig.JSON_FILE.exists()


def test_load_items_game_cleaned(tmp_path, monkeypatch):
    cleaned = tmp_path / "items_game_cleaned.json"
    cleaned.write_text(json.dumps({"1": {"name": "One"}}))
    monkeypatch.setattr(ig, "CLEANED_FILE", cleaned)
    ig.ITEM_BY_DEFINDEX.clear()
    ig.load_items_game_cleaned()
    assert ig.ITEM_BY_DEFINDEX["1"]["name"] == "One"


def test_load_items_game_cleaned_builds(tmp_path, monkeypatch):
    raw_path = tmp_path / "items_game.txt"
    monkeypatch.setattr(ig, "RAW_FILE", raw_path)
    monkeypatch.setattr(ig, "CLEANED_FILE", tmp_path / "items_game_cleaned.json")

    class DummyResp2:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        ig.requests,
        "get",
        lambda url, timeout: DummyResp2(
            '"items_game"\n{\n "items"\n {\n  "1"\n  {\n   "name" "One"\n  }\n }\n}\n'
        ),
    )
    ig.ITEM_BY_DEFINDEX.clear()
    data = ig.load_items_game_cleaned(force_rebuild=True)
    assert data["1"]["name"] == "One"
    assert ig.CLEANED_FILE.exists()
