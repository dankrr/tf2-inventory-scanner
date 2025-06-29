import json

import utils.autobot_schema_cache as ac


def test_ensure_all_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "SCHEMA_DIR", tmp_path / "schema")
    monkeypatch.setattr(ac, "ITEMS_GAME_DIR", tmp_path / "items_game")
    monkeypatch.setattr(ac, "PROPERTIES_DIR", tmp_path / "properties")
    monkeypatch.setattr(ac, "GRADES_DIR", tmp_path / "grades")
    monkeypatch.setattr(ac, "SCHEMA_KEYS", ["items"])
    monkeypatch.setattr(ac, "ITEMS_GAME_KEYS", ["items"])
    monkeypatch.setattr(ac, "PROPERTIES_KEYS", ["defindexes"])
    monkeypatch.setattr(ac, "CLASS_NAMES", [])
    monkeypatch.setattr(ac, "GRADE_ENDPOINTS", ["v1"])
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

    assert (tmp_path / "properties" / "defindexes.json").exists()
    assert (tmp_path / "grades" / "v1.json").exists()
    assert (tmp_path / "schema" / "items.json").exists()
    assert (tmp_path / "items_game" / "items.json").exists()
    assert calls


def test_cache_hit(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "SCHEMA_DIR", tmp_path / "schema")
    monkeypatch.setattr(ac, "ITEMS_GAME_DIR", tmp_path / "items_game")
    monkeypatch.setattr(ac, "PROPERTIES_DIR", tmp_path / "properties")
    monkeypatch.setattr(ac, "GRADES_DIR", tmp_path / "grades")
    monkeypatch.setattr(ac, "SCHEMA_KEYS", [])
    monkeypatch.setattr(ac, "ITEMS_GAME_KEYS", [])
    monkeypatch.setattr(ac, "PROPERTIES_KEYS", ["defindexes"])
    monkeypatch.setattr(ac, "CLASS_NAMES", [])
    monkeypatch.setattr(ac, "GRADE_ENDPOINTS", [])
    monkeypatch.setattr(
        ac.items_game_cache, "JSON_FILE", tmp_path / "items_game_cleaned.json"
    )
    (tmp_path / "items_game_cleaned.json").write_text("{}")

    (tmp_path / "properties" / "defindexes.json").parent.mkdir(parents=True)
    (tmp_path / "properties" / "defindexes.json").write_text(json.dumps({"x": 1}))

    monkeypatch.setattr(
        ac,
        "_fetch_json",
        lambda url: (_ for _ in ()).throw(AssertionError("should not fetch")),
    )

    ac.ensure_all_cached()


def test_class_aliases(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "SCHEMA_DIR", tmp_path / "schema")
    monkeypatch.setattr(ac, "ITEMS_GAME_DIR", tmp_path / "items_game")
    monkeypatch.setattr(ac, "PROPERTIES_DIR", tmp_path / "properties")
    monkeypatch.setattr(ac, "GRADES_DIR", tmp_path / "grades")
    monkeypatch.setattr(ac, "PROPERTIES_KEYS", [])
    monkeypatch.setattr(ac, "GRADE_ENDPOINTS", [])
    monkeypatch.setattr(ac, "SCHEMA_KEYS", [])
    monkeypatch.setattr(ac, "ITEMS_GAME_KEYS", [])
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

    assert (tmp_path / "properties" / "craftWeaponsByClass_Demoman.json").exists()
    assert (tmp_path / "properties" / "craftWeaponsByClass_Engineer.json").exists()
    assert any("Demoman" in u for u in captured)
    assert any("Engineer" in u for u in captured)


def test_unknown_class_ignored(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "SCHEMA_DIR", tmp_path / "schema")
    monkeypatch.setattr(ac, "ITEMS_GAME_DIR", tmp_path / "items_game")
    monkeypatch.setattr(ac, "PROPERTIES_DIR", tmp_path / "properties")
    monkeypatch.setattr(ac, "GRADES_DIR", tmp_path / "grades")
    monkeypatch.setattr(ac, "PROPERTIES_KEYS", [])
    monkeypatch.setattr(ac, "GRADE_ENDPOINTS", [])
    monkeypatch.setattr(ac, "SCHEMA_KEYS", [])
    monkeypatch.setattr(ac, "ITEMS_GAME_KEYS", [])
    monkeypatch.setattr(ac, "CLASS_NAMES", ["xyz"])

    monkeypatch.setattr(ac.items_game_cache, "update_items_game", lambda: None)
    monkeypatch.setattr(
        ac.items_game_cache, "JSON_FILE", tmp_path / "items_game_cleaned.json"
    )

    monkeypatch.setattr(ac, "_fetch_json", lambda url: {})

    ac.ensure_all_cached(refresh=True)

    assert not list(tmp_path.iterdir())


def test_404_warning(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "SCHEMA_DIR", tmp_path / "schema")
    monkeypatch.setattr(ac, "ITEMS_GAME_DIR", tmp_path / "items_game")
    monkeypatch.setattr(ac, "PROPERTIES_DIR", tmp_path / "properties")
    monkeypatch.setattr(ac, "GRADES_DIR", tmp_path / "grades")
    monkeypatch.setattr(ac, "SCHEMA_KEYS", ["missing"])
    monkeypatch.setattr(ac, "ITEMS_GAME_KEYS", [])
    monkeypatch.setattr(ac, "PROPERTIES_KEYS", [])
    monkeypatch.setattr(ac, "CLASS_NAMES", [])
    monkeypatch.setattr(ac, "GRADE_ENDPOINTS", [])
    monkeypatch.setattr(ac.items_game_cache, "update_items_game", lambda: None)
    monkeypatch.setattr(
        ac.items_game_cache, "JSON_FILE", tmp_path / "items_game_cleaned.json"
    )
    (tmp_path / "items_game_cleaned.json").write_text("{}")

    from types import SimpleNamespace
    import requests

    def fake_fetch(url):
        resp = SimpleNamespace(status_code=404)
        raise requests.HTTPError(response=resp)

    monkeypatch.setattr(ac, "_fetch_json", fake_fetch)

    ac.ensure_all_cached(refresh=True)

    assert not (tmp_path / "schema" / "missing.json").exists()
