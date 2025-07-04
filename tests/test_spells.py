import utils.inventory_processor as ip
from utils.inventory_processor import _extract_spells
from utils import local_data as ld


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

    dummy = {
        "attributes": [
            {"defindex": 1009},
            {"defindex": 2000},
            {"defindex": 2001},
            {"defindex": 1010},
            {"defindex": 3003},
        ]
    }
    badges, names = _extract_spells(dummy)
    assert set(names) == {
        "Exorcism",
        "Halloween Footprints",
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
    monkeypatch.setattr(ld, "FOOTPRINT_SPELL_MAP", {3: "Gangreen Footprints"}, False)
    monkeypatch.setattr(ip, "FOOTPRINT_SPELL_MAP", {3: "Gangreen Footprints"}, False)
    monkeypatch.setattr(
        ld,
        "PAINT_SPELL_MAP",
        {1: "Paint A", 2: "Paint B", 3: "Paint C", 4: "Paint D"},
        False,
    )
    monkeypatch.setattr(
        ip,
        "PAINT_SPELL_MAP",
        {1: "Paint A", 2: "Paint B", 3: "Paint C", 4: "Paint D"},
        False,
    )

    dummy = {
        "attributes": [
            {"defindex": 4001, "value": 1},
            {"defindex": 4002, "value": 2},
            {"defindex": 4003, "value": 3},
            {"defindex": 4004, "value": 4},
            {"defindex": 2000, "value": 3},
        ]
    }
    _, names = _extract_spells(dummy)
    assert {
        "Paint A",
        "Paint B",
        "Paint C",
        "Paint D",
        "Gangreen Footprints",
    } <= set(names)
