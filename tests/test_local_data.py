import json
import pytest

from utils import local_data as ld


def test_load_files_success(tmp_path, monkeypatch, capsys):
    schema_file = tmp_path / "items.json"
    items_file = tmp_path / "ig_items.json"
    effects_file = tmp_path / "effects.json"
    schema_file.write_text(json.dumps({"1": {"name": "One"}}))
    items_file.write_text(json.dumps({"items": {"1": {"name": "A"}}}))
    effects_file.write_text(json.dumps({}))
    monkeypatch.setattr(ld, "SCHEMA_ITEMS_FILE", schema_file)
    monkeypatch.setattr(ld, "ITEMS_GAME_FILE", items_file)
    monkeypatch.setattr(ld, "EFFECTS_FILE", effects_file)
    ld.TF2_SCHEMA = {}
    ld.ITEMS_GAME_CLEANED = {}
    ld.EFFECT_NAMES = {}
    ld.load_files()
    out = capsys.readouterr().out
    assert ld.TF2_SCHEMA["1"]["name"] == "One"
    assert f"Loaded 1 items from {schema_file}" in out
    assert "schema/items.json may be stale" in out


def test_load_files_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(ld, "SCHEMA_ITEMS_FILE", tmp_path / "missing.json")
    monkeypatch.setattr(ld, "ITEMS_GAME_FILE", tmp_path / "missing2.json")
    monkeypatch.setattr(ld, "EFFECTS_FILE", tmp_path / "missing3.json")
    with pytest.raises(RuntimeError):
        ld.load_files()


def test_clean_items_game_parses_all():
    sample = {
        "items_game": {
            "items": {
                "111": {"name": "Correct"},
                "30607": {"name": "Pump"},
            }
        }
    }
    cleaned = ld.clean_items_game(sample)
    assert cleaned["111"]["name"] == "Correct"
    assert cleaned["30607"]["name"] == "Pump"
