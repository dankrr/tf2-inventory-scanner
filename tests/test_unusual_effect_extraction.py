from utils.inventory_processor import _extract_unusual_effect, EFFECTS_MAP
from utils import local_data


def test_extract_unusual_effect_cosmetic():
    EFFECTS_MAP[350] = "Spectral Fire"
    asset = {"quality": 5, "attributes": [{"defindex": 134, "float_value": 350}]}
    assert _extract_unusual_effect(asset) == {"id": 350, "name": "Spectral Fire"}


def test_extract_unusual_effect_unusual():
    EFFECTS_MAP[510] = "Test Name"
    asset = {"quality": 5, "attributes": [{"defindex": 2041, "value": 510}]}
    assert _extract_unusual_effect(asset) == {"id": 510, "name": "Test Name"}


def test_extract_unusual_effect_value_fallback():
    EFFECTS_MAP[3042] = "Taunt Effect"
    local_data.EFFECT_NAMES.pop("3042", None)
    asset = {
        "quality": 5,
        "attributes": [
            {"defindex": 2041, "float_value": 4.2627499284760935e-42, "value": 3042}
        ],
    }
    assert _extract_unusual_effect(asset) == {"id": 3042, "name": "Taunt Effect"}


def test_extract_unusual_effect_zero_skipped():
    asset = {"quality": 5, "attributes": [{"defindex": 2041, "float_value": 0}]}
    assert _extract_unusual_effect(asset) is None


def test_no_effect():
    asset = {"quality": 5, "attributes": []}
    assert _extract_unusual_effect(asset) is None
