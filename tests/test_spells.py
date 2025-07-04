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
