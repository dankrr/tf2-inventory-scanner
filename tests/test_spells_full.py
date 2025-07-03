from utils.inventory_processor import _extract_spells


def test_weapon_and_cosmetic_spells():
    dummy = {
        "attributes": [
            {"defindex": 1005, "value": 1},  # Pumpkin Bombs
            {"defindex": 134, "value": 701},  # Chromatic Corruption
            {"defindex": 134, "value": 3005},  # Bruised Purple Footprints
            {"defindex": 1004, "value": 2},  # Voices from Below
            {"defindex": 2043, "value": 3100495},  # Die Job
        ]
    }
    badges, names = _extract_spells(dummy, is_weapon=False)
    assert names == ["Chromatic Corruption", "Bruised Purple Footprints"]
    assert len(badges) == 2
