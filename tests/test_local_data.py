import json
import pytest

from utils import local_data as ld


def test_load_files_success(tmp_path, monkeypatch, capsys):
    attr_file = tmp_path / "attributes.json"
    particles_file = tmp_path / "particles.json"
    items_file = tmp_path / "items.json"
    qual_file = tmp_path / "qualities.json"
    lookups_file = tmp_path / "string_lookups.json"

    attr_file.write_text(json.dumps([{"defindex": 1, "name": "Attr"}]))
    particles_file.write_text(json.dumps([{"id": 1, "name": "P"}]))
    items_file.write_text(json.dumps([{"defindex": 1, "name": "One"}]))
    qual_file.write_text(json.dumps({"1": "Unique"}))

    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", attr_file)
    monkeypatch.setattr(ld, "PARTICLES_FILE", particles_file)
    monkeypatch.setattr(ld, "ITEMS_FILE", items_file)
    monkeypatch.setattr(ld, "QUALITIES_FILE", qual_file)
    monkeypatch.setattr(ld, "STRING_LOOKUPS_FILE", lookups_file)

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
    lookups_file = tmp_path / "string_lookups.json"

    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", attr_file)
    monkeypatch.setattr(ld, "PARTICLES_FILE", particles_file)
    monkeypatch.setattr(ld, "ITEMS_FILE", items_file)
    monkeypatch.setattr(ld, "QUALITIES_FILE", qual_file)
    monkeypatch.setattr(ld, "STRING_LOOKUPS_FILE", lookups_file)

    payloads = {
        "attributes": [{"defindex": 1, "name": "Attr"}],
        "items": [{"defindex": 1, "name": "One"}],
        "particles": [{"id": 1, "name": "P"}],
        "qualities": {"1": "Unique"},
        "string_lookups": {
            "value": [
                {
                    "table_name": "SPELL: set item tint RGB",
                    "strings": [{"index": 0, "string": "A"}],
                }
            ]
        },
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
    ld.PAINT_SPELL_MAP = {}
    ld.FOOTPRINT_SPELL_MAP = {}

    ld.load_files(auto_refetch=True)
    out = capsys.readouterr().out
    assert "Downloaded" in out
    assert ld.SCHEMA_ATTRIBUTES[1]["name"] == "Attr"
    assert ld.PAINT_SPELL_MAP == {0: "A"}


def test_load_files_name_key_quality(tmp_path, monkeypatch):
    attr_file = tmp_path / "attributes.json"
    particles_file = tmp_path / "particles.json"
    items_file = tmp_path / "items.json"
    qual_file = tmp_path / "qualities.json"

    attr_file.write_text(json.dumps([{"defindex": 1, "name": "Attr"}]))
    particles_file.write_text(json.dumps([{"id": 1, "name": "P"}]))
    items_file.write_text(json.dumps([{"defindex": 1, "name": "One"}]))
    qual_file.write_text(json.dumps({"Unique": 1}))

    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", attr_file)
    monkeypatch.setattr(ld, "PARTICLES_FILE", particles_file)
    monkeypatch.setattr(ld, "ITEMS_FILE", items_file)
    monkeypatch.setattr(ld, "QUALITIES_FILE", qual_file)

    ld.SCHEMA_ATTRIBUTES = {}
    ld.ITEMS_BY_DEFINDEX = {}
    ld.PARTICLE_NAMES = {}
    ld.QUALITIES_BY_INDEX = {}

    ld.load_files()
    assert ld.QUALITIES_BY_INDEX == {1: "Unique"}


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


def test_load_files_string_lookups(tmp_path, monkeypatch):
    attr_file = tmp_path / "attributes.json"
    particles_file = tmp_path / "particles.json"
    items_file = tmp_path / "items.json"
    qual_file = tmp_path / "qualities.json"
    lookups_file = tmp_path / "string_lookups.json"

    for f in (attr_file, particles_file, items_file, qual_file):
        f.write_text("[]")

    lookups = {
        "value": [
            {
                "table_name": "SPELL: set item tint RGB",
                "strings": [
                    {"index": 0, "string": "A"},
                    {"index": 1, "string": "B"},
                ],
            },
            {
                "table_name": "SPELL: set Halloween footstep type",
                "strings": [
                    {"index": 2, "string": "C"},
                    {"index": 3, "string": "D"},
                ],
            },
        ]
    }
    lookups_file.write_text(json.dumps(lookups))

    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", attr_file)
    monkeypatch.setattr(ld, "PARTICLES_FILE", particles_file)
    monkeypatch.setattr(ld, "ITEMS_FILE", items_file)
    monkeypatch.setattr(ld, "QUALITIES_FILE", qual_file)
    monkeypatch.setattr(ld, "STRING_LOOKUPS_FILE", lookups_file)

    ld.FOOTPRINT_SPELL_MAP = {}
    ld.PAINT_SPELL_MAP = {}

    ld.load_files()

    assert ld.PAINT_SPELL_MAP == {0: "A", 1: "B"}
    assert ld.FOOTPRINT_SPELL_MAP == {2: "C", 3: "D"}


def test_load_files_string_lookups_missing(tmp_path, monkeypatch):
    attr_file = tmp_path / "attributes.json"
    particles_file = tmp_path / "particles.json"
    items_file = tmp_path / "items.json"
    qual_file = tmp_path / "qualities.json"

    for f in (attr_file, particles_file, items_file, qual_file):
        f.write_text("[]")

    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", attr_file)
    monkeypatch.setattr(ld, "PARTICLES_FILE", particles_file)
    monkeypatch.setattr(ld, "ITEMS_FILE", items_file)
    monkeypatch.setattr(ld, "QUALITIES_FILE", qual_file)
    monkeypatch.setattr(ld, "STRING_LOOKUPS_FILE", tmp_path / "missing.json")

    ld.FOOTPRINT_SPELL_MAP = {1: "X"}
    ld.PAINT_SPELL_MAP = {1: "Y"}

    ld.load_files()

    assert ld.PAINT_SPELL_MAP == {}
    assert ld.FOOTPRINT_SPELL_MAP == {}
