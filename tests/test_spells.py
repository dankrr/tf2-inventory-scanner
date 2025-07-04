from utils.inventory_processor import _extract_spells
from utils import local_data as ld


def test_all_spell_types(monkeypatch):
    monkeypatch.setattr(
        ld,
        "SCHEMA_ATTRIBUTES",
        {
            1009: {
                "description_string": "Exorcism",
                "attribute_class": "halloween_death_ghosts",
            },
            2000: {
                "description_string": "Bruised Purple Footprints",
                "attribute_class": "halloween_footstep_type",
            },
            2001: {
                "description_string": "Spectral Spectrum",
                "attribute_class": "halloween_green_flames",
            },
            1010: {
                "description_string": "Spy's Creepy Croon",
                "attribute_class": "halloween_voice_modulation",
            },
            3003: {
                "description_string": "Squash Rockets",
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
