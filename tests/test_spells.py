from utils.inventory_processor import _extract_spells


def test_all_spell_types():
    dummy = {
        "attributes": [
            {"defindex": 1007, "value": 1},  # Exorcism
            {"defindex": 134, "value": 3005},  # Bruised Purple Footprints
            {"defindex": 134, "value": 702},  # Spectral Spectrum
            {"defindex": 1004, "value": 9},  # Voices from Below
            {"defindex": 3002, "value": 1},  # Squash Rockets
        ]
    }
    badges, names = _extract_spells(dummy)
    assert "Exorcism" in names
    assert "Spectral Spectrum" in names
    assert "Bruised Purple Footprints" in names
    assert "Voices from Below" in names
    assert "Squash Rockets" in names
    assert any(b["icon"] == "👻" for b in badges)


def test_invalid_spell_values():
    dummy = {
        "attributes": [
            {"defindex": 134, "value": "10 0 -7"},
            {"defindex": 1005, "value": 1},
        ]
    }
    badges, names = _extract_spells(dummy)
    assert "Pumpkin Bombs" in names
    assert len(names) == 1
