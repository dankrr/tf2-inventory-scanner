from utils.inventory_processor import _extract_spells


def test_type_filter():
    # fake weapon asset
    weapon = {
        "attributes": [
            {"defindex": 1005, "value": 1},
            {"defindex": 134, "value": 701},
        ]
    }
    b, n = _extract_spells(weapon, is_weapon=True)
    assert "Pumpkin Bombs" in n and "Chromatic Corruption" not in n

    # fake cosmetic asset
    hat = {
        "attributes": [
            {"defindex": 134, "value": 701},
            {"defindex": 1005, "value": 1},
        ]
    }
    b, n = _extract_spells(hat, is_weapon=False)
    assert "Chromatic Corruption" in n and "Pumpkin Bombs" not in n

    # verify cap of 2
    big = {
        "attributes": [
            {"defindex": 1005, "value": 1},
            {"defindex": 1006, "value": 1},
            {"defindex": 1007, "value": 1},
        ]
    }
    b, n = _extract_spells(big, is_weapon=True)
    assert len(n) == 2
