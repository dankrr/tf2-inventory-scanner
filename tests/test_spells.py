from utils.inventory_processor import _extract_spells


def test_extract_spells_simple():
    asset = {
        "attributes": [
            {"defindex": 1004, "float_value": 1},
            {"defindex": 1009, "value": 1},
        ]
    }
    badges, names = _extract_spells(asset)
    assert "Chromatic Corruption" in names
    assert "Exorcism" in names
    assert any(isinstance(b, dict) for b in badges)


def test_unknown_spell_value():
    asset = {"attributes": [{"defindex": 1004, "float_value": 99}]}
    badges, names = _extract_spells(asset)
    assert badges == []
    assert names == []
