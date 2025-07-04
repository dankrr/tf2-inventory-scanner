from utils.inventory_processor import _extract_spells
from utils import local_data as ld


def test_all_spell_types(monkeypatch):
    monkeypatch.setattr(
        ld,
        "SCHEMA_ATTRIBUTES",
        {
            1009: {"name": "Exorcism", "attribute_class": "halloween_death_ghosts"},
            2000: {
                "name": "Bruised Purple Footprints",
                "attribute_class": "halloween_footstep_type",
            },
            2001: {
                "name": "Spectral Spectrum",
                "attribute_class": "halloween_green_flames",
            },
            1010: {
                "name": "Spy's Creepy Croon",
                "attribute_class": "halloween_voice_modulation",
            },
            3003: {
                "name": "Squash Rockets",
                "attribute_class": "halloween_pumpkin_explosions",
            },
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
    assert "Exorcism" in names
    assert "Spectral Spectrum" in names
    assert "Bruised Purple Footprints" in names
    assert "Spy's Creepy Croon" in names
    assert "Squash Rockets" in names
    assert any(b["icon"] == "👻" for b in badges)


def test_placeholder_spell_ignored(monkeypatch):
    monkeypatch.setattr(
        ld,
        "SCHEMA_ATTRIBUTES",
        {
            9999: {"name": "%s1", "attribute_class": "halloween_green_flames"},
        },
        False,
    )

    dummy = {"attributes": [{"defindex": 9999}]}
    badges, names = _extract_spells(dummy)
    assert badges == []
    assert names == []
