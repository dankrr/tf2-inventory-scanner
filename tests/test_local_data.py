import json
import pytest

from utils import local_data as ld


def test_load_files_success(tmp_path, monkeypatch, capsys):
    attr_file = tmp_path / "attributes.json"
    particles_file = tmp_path / "particles.json"
    items_file = tmp_path / "items.json"
    qual_file = tmp_path / "qualities.json"

    attr_file.write_text(json.dumps([{"defindex": 1, "name": "Attr"}]))
    particles_file.write_text(json.dumps([{"id": 1, "name": "P"}]))
    items_file.write_text(json.dumps([{"defindex": 1, "name": "One"}]))
    qual_file.write_text(json.dumps({"1": "Unique"}))

    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", attr_file)
    monkeypatch.setattr(ld, "PARTICLES_FILE", particles_file)
    monkeypatch.setattr(ld, "ITEMS_FILE", items_file)
    monkeypatch.setattr(ld, "QUALITIES_FILE", qual_file)

    ld.SCHEMA_ATTRIBUTES = {}
    ld.ITEMS_BY_DEFINDEX = {}
    ld.PARTICLE_NAMES = {}
    ld.QUALITIES_BY_INDEX = {}
    ld.EFFECT_NAMES = {}

    ld.load_files()
    out = capsys.readouterr().out
    assert ld.SCHEMA_ATTRIBUTES[1]["name"] == "Attr"
    assert ld.ITEMS_BY_DEFINDEX[1]["name"] == "One"
    assert "Loaded 1 attributes" in out


def test_load_files_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", tmp_path / "missing.json")
    monkeypatch.setattr(ld, "ITEMS_FILE", tmp_path / "missing2.json")
    with pytest.raises(RuntimeError):
        ld.load_files()


def test_load_files_auto_refetch(tmp_path, monkeypatch, capsys):
    attr_file = tmp_path / "attributes.json"
    items_file = tmp_path / "items.json"
    particles_file = tmp_path / "particles.json"
    qual_file = tmp_path / "qualities.json"

    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", attr_file)
    monkeypatch.setattr(ld, "PARTICLES_FILE", particles_file)
    monkeypatch.setattr(ld, "ITEMS_FILE", items_file)
    monkeypatch.setattr(ld, "QUALITIES_FILE", qual_file)

    payloads = {
        "attributes": [{"defindex": 1, "name": "Attr"}],
        "items": [{"defindex": 1, "name": "One"}],
        "particles": [{"id": 1, "name": "P"}],
        "qualities": {"1": "Unique"},
    }

    def fake_fetch(self, endpoint):
        for key, ep in ld.SchemaProvider.ENDPOINTS.items():
            if endpoint == ep:
                return payloads[key]
        raise KeyError(endpoint)

    monkeypatch.setattr(ld.SchemaProvider, "_fetch", fake_fetch)

    ld.SCHEMA_ATTRIBUTES = {}
    ld.ITEMS_BY_DEFINDEX = {}
    ld.PARTICLE_NAMES = {}
    ld.QUALITIES_BY_INDEX = {}

    ld.load_files(auto_refetch=True)
    out = capsys.readouterr().out
    assert "Downloaded" in out
    assert ld.SCHEMA_ATTRIBUTES[1]["name"] == "Attr"


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
