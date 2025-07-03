from utils.inventory_processor import _extract_spells


def test_all_spell_types():
    dummy = {
        "attributes": [
            {"defindex": 1009, "value": 1},  # Exorcism
            {"defindex": 2000, "value": 4},  # Bruised Purple Footprints
            {"defindex": 2001, "value": 5},  # Spectral Spectrum
            {"defindex": 1010, "value": 9},  # Spy's Creepy Croon
            {"defindex": 3003, "value": 1},  # Squash Rockets
        ]
    }
    badges, names = _extract_spells(dummy)
    assert "Exorcism" in names
    assert "Spectral Spectrum" in names
    assert "Bruised Purple Footprints" in names
    assert "Spy's Creepy Croon" in names
    assert "Squash Rockets" in names
    assert any(b["icon"] == "👻" for b in badges)
