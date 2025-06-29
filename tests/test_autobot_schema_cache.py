import json

import utils.autobot_schema_cache as ac


def test_ensure_all_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(ac, "PROPERTIES", {"defindexes": "defindexes.json"})
    monkeypatch.setattr(ac, "CLASS_NAMES", [])
    monkeypatch.setattr(ac, "GRADE_FILES", {"v1": "item_grade_v1.json"})
    monkeypatch.setattr(ac, "BASE_ENDPOINTS", {"tf2schema.json": "/schema"})
    monkeypatch.setattr(ac.items_game_cache, "update_items_game", lambda: None)
    monkeypatch.setattr(
        ac.items_game_cache, "JSON_FILE", tmp_path / "items_game_cleaned.json"
    )
    (tmp_path / "items_game_cleaned.json").write_text("{}")

    calls = []

    def fake_fetch(url):
        calls.append(url)
        return {"ok": True}

    monkeypatch.setattr(ac, "_fetch_json", fake_fetch)

    ac.ensure_all_cached(refresh=True)

    assert (tmp_path / "defindexes.json").exists()
    assert (tmp_path / "item_grade_v1.json").exists()
    assert (tmp_path / "tf2schema.json").exists()
    assert calls


def test_cache_hit(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(ac, "PROPERTIES", {"defindexes": "defindexes.json"})
    monkeypatch.setattr(ac, "CLASS_NAMES", [])
    monkeypatch.setattr(ac, "GRADE_FILES", {})
    monkeypatch.setattr(ac, "BASE_ENDPOINTS", {})
    monkeypatch.setattr(
        ac.items_game_cache, "JSON_FILE", tmp_path / "items_game_cleaned.json"
    )
    (tmp_path / "items_game_cleaned.json").write_text("{}")

    (tmp_path / "defindexes.json").write_text(json.dumps({"x": 1}))

    monkeypatch.setattr(
        ac,
        "_fetch_json",
        lambda url: (_ for _ in ()).throw(AssertionError("should not fetch")),
    )

    ac.ensure_all_cached()


def test_class_aliases(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(ac, "PROPERTIES", {})
    monkeypatch.setattr(ac, "GRADE_FILES", {})
    monkeypatch.setattr(ac, "BASE_ENDPOINTS", {})
    monkeypatch.setattr(ac, "CLASS_NAMES", ["Demo", "Engie"])
    monkeypatch.setattr(ac.items_game_cache, "update_items_game", lambda: None)
    monkeypatch.setattr(
        ac.items_game_cache, "JSON_FILE", tmp_path / "items_game_cleaned.json"
    )

    captured = []

    def fake_fetch(url):
        captured.append(url)
        return {}

    monkeypatch.setattr(ac, "_fetch_json", fake_fetch)

    ac.ensure_all_cached(refresh=True)

    assert (tmp_path / "craftWeaponsByClass_Demoman.json").exists()
    assert (tmp_path / "craftWeaponsByClass_Engineer.json").exists()
    assert any("Demoman" in u for u in captured)
    assert any("Engineer" in u for u in captured)


def test_unknown_class_ignored(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(ac, "PROPERTIES", {})
    monkeypatch.setattr(ac, "GRADE_FILES", {})
    monkeypatch.setattr(ac, "BASE_ENDPOINTS", {})
    monkeypatch.setattr(ac, "CLASS_NAMES", ["xyz"])

    monkeypatch.setattr(ac.items_game_cache, "update_items_game", lambda: None)
    monkeypatch.setattr(
        ac.items_game_cache, "JSON_FILE", tmp_path / "items_game_cleaned.json"
    )

    monkeypatch.setattr(ac, "_fetch_json", lambda url: {})

    ac.ensure_all_cached(refresh=True)

    assert not list(tmp_path.iterdir())
