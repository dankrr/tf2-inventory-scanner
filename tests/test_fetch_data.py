import json

import scripts.fetch_data as fd


def test_fetch_items_game(tmp_path, monkeypatch):
    captured = {"url": None}

    class DummyResp:
        text = "content"

        def raise_for_status(self):
            pass

    def fake_get(url, timeout):
        captured["url"] = url
        return DummyResp()

    monkeypatch.setattr(fd.requests, "get", fake_get)
    monkeypatch.setattr(fd, "CACHE_DIR", tmp_path)
    path = fd.fetch_items_game()
    assert path == tmp_path / "items_game.txt"
    assert path.read_text() == "content"
    assert captured["url"] == fd.ITEMS_GAME_URL


def test_fetch_autobot_schema(tmp_path, monkeypatch):
    class DummyResp:
        def __init__(self):
            self.payload = {"a": 1}

        def raise_for_status(self):
            pass

        def json(self):
            return self.payload

    def fake_get(url, timeout):
        return DummyResp()

    monkeypatch.setattr(fd.requests, "get", fake_get)
    monkeypatch.setattr(fd, "CACHE_DIR", tmp_path)
    path = fd.fetch_autobot_schema()
    assert path.exists()
    assert json.loads(path.read_text()) == {"a": 1}


def test_fetch_autobot_properties(tmp_path, monkeypatch):
    def fake_get(url, timeout):
        class DummyResp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"n": url}

        return DummyResp()

    monkeypatch.setattr(fd.requests, "get", fake_get)
    monkeypatch.setattr(fd, "CACHE_DIR", tmp_path)
    paths = fd.fetch_autobot_properties()
    assert len(paths) == len(fd.PROPERTIES)
    for path in paths:
        assert path.exists()
        data = json.loads(path.read_text())
        assert "properties" not in data  # just ensure content wrote
