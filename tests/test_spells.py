import utils.inventory_processor as ip
from utils.inventory_processor import _extract_spells
from utils import local_data as ld
from utils import constants


def _parse_lookups(data):
    foot_map = {}
    paint_map = {}
    tables = data.get("value", data)
    for table in tables:
        if not isinstance(table, dict):
            continue
        name = str(table.get("table_name", "")).lower()
        entries = table.get("strings", [])
        if not isinstance(entries, list):
            continue
        mapping = {
            int(e["index"]): str(e["string"])
            for e in entries
            if isinstance(e, dict)
            and "index" in e
            and "string" in e
            and str(e["index"]).lstrip("-").isdigit()
        }
        if "footstep" in name or "footprint" in name:
            foot_map.update(mapping)
        elif "tint" in name:
            paint_map.update(mapping)
    return foot_map, paint_map


def test_all_spell_types(monkeypatch):
    monkeypatch.setattr(
        ld,
        "SCHEMA_ATTRIBUTES",
        {
            1009: {
                "name": "SPELL: Halloween ghosts",
                "attribute_class": "halloween_death_ghosts",
            },
            2000: {
                "name": "SPELL: set Halloween footstep type",
                "attribute_class": "halloween_footstep_type",
            },
            2001: {
                "name": "SPELL: Halloween fire",
                "attribute_class": "halloween_green_flames",
            },
            1010: {
                "name": "SPELL: Halloween voice modulation",
                "attribute_class": "halloween_voice_modulation",
            },
            3003: {
                "name": "SPELL: Pumpkin explosions",
                "attribute_class": "halloween_pumpkin_explosions",
            },
        },
        False,
    )
    monkeypatch.setattr(
        ld,
        "SPELL_DISPLAY_NAMES",
        {
            "halloween_death_ghosts": "Exorcism",
            "halloween_footstep_type": "Halloween Footprints",
            "halloween_green_flames": "Halloween Fire",
            "halloween_voice_modulation": "Voices From Below",
            "halloween_pumpkin_explosions": "Pumpkin Bombs",
        },
        False,
    )

    lookups = {
        "value": [
            {
                "table_name": "SPELL: set item tint RGB",
                "strings": [
                    {"index": 1, "string": "Paint A"},
                    {"index": 2, "string": "Paint B"},
                ],
            },
            {
                "table_name": "SPELL: set Halloween footstep type",
                "strings": [
                    {"index": 30, "string": "Gangreen Footprints"},
                ],
            },
        ]
    }
    foot_map, paint_map = _parse_lookups(lookups)
    spell_map = {
        **{k: ("paint", v) for k, v in paint_map.items()},
        **{k: ("footprint", v) for k, v in foot_map.items()},
    }
    monkeypatch.setattr(ip, "_SPELL_MAP", spell_map, False)

    dummy = {
        "attributes": [
            {"defindex": 1009},
            {"defindex": 2000, "value": 30},
            {"defindex": 2001},
            {"defindex": 1010},
            {"defindex": 3003},
        ]
    }
    badges, names = _extract_spells(dummy)
    assert set(names) == {
        "Exorcism",
        foot_map[30],
        "Halloween Fire",
        "Voices From Below",
        "Pumpkin Bombs",
    }
    assert any(b["icon"] == "👻" for b in badges)


def test_placeholder_spell_ignored(monkeypatch):
    monkeypatch.setattr(
        ld,
        "SCHEMA_ATTRIBUTES",
        {
            9999: {"name": "SPELL: Unknown", "attribute_class": "unused_spell"},
        },
        False,
    )
    monkeypatch.setattr(ld, "SPELL_DISPLAY_NAMES", {}, False)

    dummy = {"attributes": [{"defindex": 9999}]}
    badges, names = _extract_spells(dummy)
    assert badges == []
    assert names == []


def test_paint_and_footprints(monkeypatch):
    monkeypatch.setattr(
        ld,
        "SCHEMA_ATTRIBUTES",
        {
            4001: {
                "name": "SPELL: Paint A",
                "attribute_class": "set_item_tint_rgb_override",
            },
            4002: {
                "name": "SPELL: Paint B",
                "attribute_class": "set_item_color_wear_override",
            },
            4003: {
                "name": "SPELL: Paint C",
                "attribute_class": "set_item_tint_rgb_unusual",
            },
            4004: {
                "name": "SPELL: Paint D",
                "attribute_class": "set_item_texture_wear_override",
            },
            2000: {
                "name": "SPELL: set Halloween footstep type",
                "attribute_class": "halloween_footstep_type",
            },
        },
        False,
    )
    display = {
        "set_item_tint_rgb_override": "Die Job",
        "set_item_color_wear_override": "Sinister Staining",
        "set_item_tint_rgb_unusual": "Chromatic Corruption",
        "set_item_texture_wear_override": "Spectral Spectrum",
        "halloween_footstep_type": "Halloween Footprints",
    }
    monkeypatch.setattr(ld, "SPELL_DISPLAY_NAMES", display, False)
    monkeypatch.setattr(ip, "SPELL_DISPLAY_NAMES", display, False)

    lookups = {
        "value": [
            {
                "table_name": "SPELL: set item tint RGB",
                "strings": [
                    {"index": 1, "string": "Paint A"},
                    {"index": 2, "string": "Paint B"},
                    {"index": 3, "string": "Paint C"},
                    {"index": 4, "string": "Paint D"},
                ],
            },
            {
                "table_name": "SPELL: set Halloween footstep type",
                "strings": [
                    {"index": 30, "string": "Gangreen Footprints"},
                ],
            },
        ]
    }
    foot_map, paint_map = _parse_lookups(lookups)
    spell_map = {
        **{k: ("paint", v) for k, v in paint_map.items()},
        **{k: ("footprint", v) for k, v in foot_map.items()},
    }
    monkeypatch.setattr(ip, "_SPELL_MAP", spell_map, False)

    dummy = {
        "attributes": [
            {"defindex": 4001, "value": 1},
            {"defindex": 4002, "value": 2},
            {"defindex": 4003, "value": 3},
            {"defindex": 4004, "value": 4},
            {"defindex": 2000, "value": 30},
        ]
    }
    _, names = _extract_spells(dummy)
    expected = set(paint_map.values()) | {foot_map[30]}
    assert expected <= set(names)


def test_color_id_spell_map(monkeypatch):
    lookups = {
        "value": [
            {
                "table_name": "SPELL: set item tint RGB",
                "strings": [
                    {"index": 3100495, "string": "unused"},
                    {"index": 8208499, "string": "unused2"},
                ],
            },
            {
                "table_name": "SPELL: set Halloween footstep type",
                "strings": [
                    {"index": 1757009, "string": "unused"},
                ],
            },
        ]
    }

    def fake_load(name):
        if name == "string_lookups":
            return lookups["value"]
        if name == "defindexes":
            return {}
        return None

    monkeypatch.setattr(ip, "_load_json", fake_load)
    ip._SPELL_MAP = None
    ip._build_spell_map()

    p1 = constants.PAINT_COLORS[3100495][0]
    p2 = constants.PAINT_COLORS[8208499][0]
    p3 = constants.PAINT_COLORS[1757009][0]

    assert ip._SPELL_MAP[3100495] == ("paint", p1)
    assert ip._SPELL_MAP[8208499] == ("paint", p2)
    assert ip._SPELL_MAP[1757009] == ("footprint", f"{p3} Footprints")
