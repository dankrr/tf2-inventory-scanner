from utils.inventory_processor import _extract_unusual_effect, EFFECTS_MAP


def test_extract_unusual_effect_cosmetic():
    EFFECTS_MAP[350] = "Spectral Fire"
    asset = {"quality": 5, "attributes": [{"defindex": 134, "float_value": 350}]}
    assert _extract_unusual_effect(asset) == {"id": 350, "name": "Spectral Fire"}


def test_extract_unusual_effect_taunt():
    EFFECTS_MAP[510] = "Test Name"
    asset = {"quality": 5, "attributes": [{"defindex": 2041, "value": 510}]}
    assert _extract_unusual_effect(asset) == {"id": 510, "name": EFFECTS_MAP[510]}


def test_no_effect():
    asset = {"quality": 5, "attributes": []}
    assert _extract_unusual_effect(asset) is None
