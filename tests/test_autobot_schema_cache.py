import json

import utils.autobot_schema_cache as ac


def test_ensure_all_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(ac, "PROPERTIES", {"defindexes": "defindexes.json"})
    monkeypatch.setattr(ac, "CLASS_CHARS", [])
    monkeypatch.setattr(ac, "GRADE_FILES", {"v1": "item_grade_v1.json"})
    monkeypatch.setattr(ac, "BASE_ENDPOINTS", {"tf2_schema.json": "/schema/download"})

    calls = []

    def fake_fetch(url):
        calls.append(url)
        return {"ok": True}

    monkeypatch.setattr(ac, "_fetch_json", fake_fetch)

    ac.ensure_all_cached()

    assert (tmp_path / "defindexes.json").exists()
    assert (tmp_path / "item_grade_v1.json").exists()
    assert (tmp_path / "tf2_schema.json").exists()
    assert calls


def test_cache_hit(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(ac, "PROPERTIES", {"defindexes": "defindexes.json"})
    monkeypatch.setattr(ac, "CLASS_CHARS", [])
    monkeypatch.setattr(ac, "GRADE_FILES", {})
    monkeypatch.setattr(ac, "BASE_ENDPOINTS", {})

    (tmp_path / "defindexes.json").write_text(json.dumps({"x": 1}))

    monkeypatch.setattr(
        ac,
        "_fetch_json",
        lambda url: (_ for _ in ()).throw(AssertionError("should not fetch")),
    )

    ac.ensure_all_cached()
