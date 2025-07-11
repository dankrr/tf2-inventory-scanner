import json
import pytest

from utils import local_data as ld


def test_load_files_success(tmp_path, monkeypatch, caplog):
    schema_file = tmp_path / "schema_steam.json"
    currencies_file = tmp_path / "currencies.json"

    schema = {
        "attributes_by_defindex": {"1": {"name": "Attr"}},
        "items_by_defindex": {"1": {"name": "One"}},
        "qualities_by_index": {"1": "Unique"},
        "particles_by_index": {"1": "P"},
        "origins_by_index": {"0": "Drop"},
    }
    schema_file.write_text(json.dumps(schema))

    monkeypatch.setattr(ld, "STEAM_SCHEMA_FILE", schema_file)
    monkeypatch.setattr(ld, "CURRENCIES_FILE", currencies_file)
    currencies_file.write_text(json.dumps({"metal": {"value_raw": 1.0}}))

    ld.SCHEMA_ATTRIBUTES = {}
    ld.ITEMS_BY_DEFINDEX = {}
    ld.PARTICLE_NAMES = {}
    ld.QUALITIES_BY_INDEX = {}
    ld.EFFECT_NAMES = {}

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
    monkeypatch.setattr(ld, "STEAM_SCHEMA_FILE", tmp_path / "missing.json")
    monkeypatch.setattr(ld, "CURRENCIES_FILE", tmp_path / "missing3.json")
    with pytest.raises(RuntimeError):
        ld.load_files()


def test_load_files_auto_refetch(tmp_path, monkeypatch, caplog):
    schema_file = tmp_path / "schema_steam.json"
    lookups_file = tmp_path / "string_lookups.json"
    currencies_file = tmp_path / "currencies.json"

    monkeypatch.setattr(ld, "STEAM_SCHEMA_FILE", schema_file)
    monkeypatch.setattr(ld, "STRING_LOOKUPS_FILE", lookups_file)
    monkeypatch.setattr(ld, "CURRENCIES_FILE", currencies_file)

    payloads = {
        "attributes_by_defindex": {"1": {"name": "Attr"}},
        "items_by_defindex": {"1": {"name": "One"}},
        "particles_by_index": {"1": "P"},
        "qualities_by_index": {"1": "Unique"},
        "origins_by_index": {"0": "Drop"},
    }

    lookups_payload = {
        "value": [
            {
                "table_name": "SPELL: set item tint RGB",
                "strings": [{"index": 0, "string": "A"}],
            }
        ]
    }

    async def fake_load_schema(self, force: bool = False, language: str = "en"):
        schema_file.write_text(json.dumps(payloads))
        return payloads

    monkeypatch.setattr(ld.SteamSchemaProvider, "load_schema", fake_load_schema)
    monkeypatch.setattr(ld.SchemaProvider, "_fetch", lambda self, ep: lookups_payload)
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
    schema_file = tmp_path / "schema_steam.json"
    currencies_file = tmp_path / "currencies.json"

    schema = {
        "attributes_by_defindex": {"1": {"name": "Attr"}},
        "items_by_defindex": {"1": {"name": "One"}},
        "qualities_by_index": {"Unique": 1},
        "particles_by_index": {"1": "P"},
        "origins_by_index": {"0": "Drop"},
    }
    schema_file.write_text(json.dumps(schema))

    monkeypatch.setattr(ld, "STEAM_SCHEMA_FILE", schema_file)
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
    schema_file = tmp_path / "schema_steam.json"
    lookups_file = tmp_path / "string_lookups.json"
    currencies_file = tmp_path / "currencies.json"

    schema = {
        "attributes_by_defindex": {},
        "items_by_defindex": {},
        "qualities_by_index": {},
        "particles_by_index": {},
        "origins_by_index": {},
    }
    schema_file.write_text(json.dumps(schema))

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

    monkeypatch.setattr(ld, "STEAM_SCHEMA_FILE", schema_file)
    monkeypatch.setattr(ld, "STRING_LOOKUPS_FILE", lookups_file)
    monkeypatch.setattr(ld, "CURRENCIES_FILE", currencies_file)

    ld.FOOTPRINT_SPELL_MAP = {}
    ld.PAINT_SPELL_MAP = {}
    currencies_file.write_text(json.dumps({"metal": {"value_raw": 1.0}}))

    ld.load_files()

    assert ld.PAINT_SPELL_MAP == {0: "A", 1: "B"}
    assert ld.FOOTPRINT_SPELL_MAP == {2: "C", 3: "D"}


def test_load_files_string_lookups_missing(tmp_path, monkeypatch):
    schema_file = tmp_path / "schema_steam.json"
    currencies_file = tmp_path / "currencies.json"

    schema = {
        "attributes_by_defindex": {},
        "items_by_defindex": {},
        "qualities_by_index": {},
        "particles_by_index": {},
        "origins_by_index": {},
    }
    schema_file.write_text(json.dumps(schema))

    monkeypatch.setattr(ld, "STEAM_SCHEMA_FILE", schema_file)
    monkeypatch.setattr(ld, "STRING_LOOKUPS_FILE", tmp_path / "missing.json")
    monkeypatch.setattr(ld, "CURRENCIES_FILE", currencies_file)

    ld.FOOTPRINT_SPELL_MAP = {1: "X"}
    ld.PAINT_SPELL_MAP = {1: "Y"}
    currencies_file.write_text(json.dumps({"metal": {"value_raw": 1.0}}))

    ld.load_files()

    assert ld.PAINT_SPELL_MAP == {}
    assert ld.FOOTPRINT_SPELL_MAP == {}


def test_effect_names_file_loaded(tmp_path, monkeypatch):
    schema_file = tmp_path / "schema_steam.json"
    currencies_file = tmp_path / "currencies.json"
    effect_file = tmp_path / "effect_names.json"

    schema = {
        "attributes_by_defindex": {},
        "items_by_defindex": {},
        "qualities_by_index": {},
        "particles_by_index": {},
        "origins_by_index": {},
    }
    schema_file.write_text(json.dumps(schema))

    effect_file.write_text(json.dumps({"3009": "Silver Cyclone"}))

    monkeypatch.setattr(ld, "STEAM_SCHEMA_FILE", schema_file)
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
