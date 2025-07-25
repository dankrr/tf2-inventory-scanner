import json
import pytest

from utils import local_data as ld


def test_load_files_success(tmp_path, monkeypatch, caplog):
    attr_file = tmp_path / "attributes.json"
    particles_file = tmp_path / "particles.json"
    items_file = tmp_path / "items.json"
    qual_file = tmp_path / "qualities.json"
    lookups_file = tmp_path / "schema" / "string_lookups.json"
    lookups_file.parent.mkdir(parents=True, exist_ok=True)
    currencies_file = tmp_path / "currencies.json"

    attr_file.write_text(json.dumps([{"defindex": 1, "name": "Attr"}]))
    particles_file.write_text(json.dumps([{"id": 1, "name": "P"}]))
    items_file.write_text(json.dumps([{"defindex": 1, "name": "One"}]))
    qual_file.write_text(json.dumps({"1": "Unique"}))

    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", attr_file)
    monkeypatch.setattr(ld, "PARTICLES_FILE", particles_file)
    monkeypatch.setattr(ld, "ITEMS_FILE", items_file)
    monkeypatch.setattr(ld, "QUALITIES_FILE", qual_file)
    monkeypatch.setattr(ld, "STRING_LOOKUPS_FILE", lookups_file)
    monkeypatch.setattr(ld, "CURRENCIES_FILE", currencies_file)

    ld.SCHEMA_ATTRIBUTES = {}
    ld.ITEMS_BY_DEFINDEX = {}
    ld.PARTICLE_NAMES = {}
    ld.QUALITIES_BY_INDEX = {}
    ld.EFFECT_NAMES = {}
    currencies_file.write_text(json.dumps({"metal": {"value_raw": 1.0}}))

    caplog.set_level("INFO")
    ld.load_files(verbose=True)
    out = caplog.text
    assert ld.SCHEMA_ATTRIBUTES[1]["name"] == "Attr"
    assert ld.ITEMS_BY_DEFINDEX[1]["name"] == "One"
    assert "Loaded 1 attributes" in out


def test_warpaint_map_reversed(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache" / "schema"
    cache_dir.mkdir(parents=True)
    (cache_dir / "warpaints.json").write_text(json.dumps({"Warhawk": 80}))

    monkeypatch.setattr(ld, "BASE_DIR", tmp_path)
    warpaints = ld.load_json("schema/warpaints.json")
    ld.PAINTKIT_NAMES = {str(k): v for k, v in warpaints.items()}
    ld.PAINTKIT_NAMES_BY_ID = {str(v): k for k, v in ld.PAINTKIT_NAMES.items()}

    assert ld.PAINTKIT_NAMES == {"Warhawk": 80}
    assert ld.PAINTKIT_NAMES_BY_ID == {"80": "Warhawk"}


def test_load_files_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", tmp_path / "missing.json")
    monkeypatch.setattr(ld, "ITEMS_FILE", tmp_path / "missing2.json")
    monkeypatch.setattr(ld, "CURRENCIES_FILE", tmp_path / "missing3.json")
    with pytest.raises(RuntimeError):
        ld.load_files()


def test_load_files_auto_refetch(tmp_path, monkeypatch, caplog):
    attr_file = tmp_path / "attributes.json"
    items_file = tmp_path / "items.json"
    particles_file = tmp_path / "particles.json"
    qual_file = tmp_path / "qualities.json"
    lookups_file = tmp_path / "schema" / "string_lookups.json"
    lookups_file.parent.mkdir(parents=True, exist_ok=True)
    currencies_file = tmp_path / "currencies.json"

    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", attr_file)
    monkeypatch.setattr(ld, "PARTICLES_FILE", particles_file)
    monkeypatch.setattr(ld, "ITEMS_FILE", items_file)
    monkeypatch.setattr(ld, "QUALITIES_FILE", qual_file)
    monkeypatch.setattr(ld, "STRING_LOOKUPS_FILE", lookups_file)
    monkeypatch.setattr(ld, "CURRENCIES_FILE", currencies_file)

    payloads = {
        "attributes": [{"defindex": 1, "name": "Attr"}],
        "items": [{"defindex": 1, "name": "One"}],
        "particles": [{"id": 1, "name": "P"}],
        "qualities": {"1": "Unique"},
        "paintkits": [],
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
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached",
        lambda refresh=True: currencies_file,
    )
    currencies_file.write_text(json.dumps({"metal": {"value_raw": 1.0}}))

    ld.SCHEMA_ATTRIBUTES = {}
    ld.ITEMS_BY_DEFINDEX = {}
    ld.PARTICLE_NAMES = {}
    ld.QUALITIES_BY_INDEX = {}
    ld.PAINT_SPELL_MAP = {}
    ld.FOOTPRINT_SPELL_MAP = {}

    caplog.set_level("INFO")
    ld.load_files(auto_refetch=True, verbose=True)
    out = caplog.text
    assert "Downloaded" in out
    assert ld.SCHEMA_ATTRIBUTES[1]["name"] == "Attr"
    assert ld.PAINT_SPELL_MAP == {0: "A"}
    assert lookups_file.exists()


def test_load_files_name_key_quality(tmp_path, monkeypatch):
    attr_file = tmp_path / "attributes.json"
    particles_file = tmp_path / "particles.json"
    items_file = tmp_path / "items.json"
    qual_file = tmp_path / "qualities.json"
    currencies_file = tmp_path / "currencies.json"

    attr_file.write_text(json.dumps([{"defindex": 1, "name": "Attr"}]))
    particles_file.write_text(json.dumps([{"id": 1, "name": "P"}]))
    items_file.write_text(json.dumps([{"defindex": 1, "name": "One"}]))
    qual_file.write_text(json.dumps({"Unique": 1}))

    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", attr_file)
    monkeypatch.setattr(ld, "PARTICLES_FILE", particles_file)
    monkeypatch.setattr(ld, "ITEMS_FILE", items_file)
    monkeypatch.setattr(ld, "QUALITIES_FILE", qual_file)
    monkeypatch.setattr(ld, "CURRENCIES_FILE", currencies_file)

    ld.SCHEMA_ATTRIBUTES = {}
    ld.ITEMS_BY_DEFINDEX = {}
    ld.PARTICLE_NAMES = {}
    ld.QUALITIES_BY_INDEX = {}
    currencies_file.write_text(json.dumps({"metal": {"value_raw": 1.0}}))

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
    lookups_file = tmp_path / "schema" / "string_lookups.json"
    lookups_file.parent.mkdir(parents=True, exist_ok=True)
    currencies_file = tmp_path / "currencies.json"

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
    monkeypatch.setattr(ld, "CURRENCIES_FILE", currencies_file)

    ld.FOOTPRINT_SPELL_MAP = {}
    ld.PAINT_SPELL_MAP = {}
    currencies_file.write_text(json.dumps({"metal": {"value_raw": 1.0}}))

    ld.load_files()

    assert ld.PAINT_SPELL_MAP == {0: "A", 1: "B"}
    assert ld.FOOTPRINT_SPELL_MAP == {2: "C", 3: "D"}


def test_load_files_string_lookups_missing(tmp_path, monkeypatch):
    attr_file = tmp_path / "attributes.json"
    particles_file = tmp_path / "particles.json"
    items_file = tmp_path / "items.json"
    qual_file = tmp_path / "qualities.json"
    currencies_file = tmp_path / "currencies.json"

    for f in (attr_file, particles_file, items_file, qual_file):
        f.write_text("[]")

    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", attr_file)
    monkeypatch.setattr(ld, "PARTICLES_FILE", particles_file)
    monkeypatch.setattr(ld, "ITEMS_FILE", items_file)
    monkeypatch.setattr(ld, "QUALITIES_FILE", qual_file)
    monkeypatch.setattr(ld, "STRING_LOOKUPS_FILE", tmp_path / "missing.json")
    monkeypatch.setattr(ld, "CURRENCIES_FILE", currencies_file)

    ld.FOOTPRINT_SPELL_MAP = {1: "X"}
    ld.PAINT_SPELL_MAP = {1: "Y"}
    currencies_file.write_text(json.dumps({"metal": {"value_raw": 1.0}}))

    ld.load_files()

    assert ld.PAINT_SPELL_MAP == {}
    assert ld.FOOTPRINT_SPELL_MAP == {}


def test_effect_names_file_loaded(tmp_path, monkeypatch):
    attr_file = tmp_path / "attributes.json"
    particles_file = tmp_path / "particles.json"
    items_file = tmp_path / "items.json"
    qual_file = tmp_path / "qualities.json"
    currencies_file = tmp_path / "currencies.json"
    effect_file = tmp_path / "effect_names.json"

    for f in (attr_file, particles_file, items_file, qual_file):
        f.write_text("[]")

    effect_file.write_text(json.dumps({"3009": "Silver Cyclone"}))

    monkeypatch.setattr(ld, "ATTRIBUTES_FILE", attr_file)
    monkeypatch.setattr(ld, "PARTICLES_FILE", particles_file)
    monkeypatch.setattr(ld, "ITEMS_FILE", items_file)
    monkeypatch.setattr(ld, "QUALITIES_FILE", qual_file)
    monkeypatch.setattr(ld, "CURRENCIES_FILE", currencies_file)
    monkeypatch.setattr(ld, "EFFECT_NAMES_FILE", effect_file)

    currencies_file.write_text(json.dumps({"metal": {"value_raw": 1.0}}))

    ld.load_files()

    assert ld.EFFECT_NAMES["3009"] == "Silver Cyclone"


def test_load_exclusions(tmp_path, monkeypatch):
    path = tmp_path / "exclusions.json"
    data = {"hidden_origins": [2], "craft_weapon_exclusions": [3]}
    path.write_text(json.dumps(data))

    monkeypatch.setattr(ld, "EXCLUSIONS_FILE", path)

    loaded = ld.load_exclusions()
    assert loaded == data


def test_cleanup_legacy_files(tmp_path, monkeypatch, capsys):
    legacy = tmp_path / "string_lookups.json"
    legacy.write_text("{}")
    monkeypatch.setattr(ld, "LEGACY_STRING_LOOKUPS_FILE", legacy)
    ld.cleanup_legacy_files(verbose=True)
    captured = capsys.readouterr().out
    assert not legacy.exists()
    assert "Removing legacy file" in captured
