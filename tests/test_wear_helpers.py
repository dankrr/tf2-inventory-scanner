import struct
import pytest

from utils.wear_helpers import _wear_tier, _decode_seed_info
from utils import local_data


def test_wear_tier_mapping():
    assert _wear_tier(0.0) == "Factory New"
    assert _wear_tier(0.1) == "Minimal Wear"
    assert _wear_tier(0.2) == "Field-Tested"
    assert _wear_tier(0.4) == "Well-Worn"
    assert _wear_tier(0.9) == "Battle Scarred"


def test_decode_seed_info_basic():
    wear_val = 0.25
    hi = struct.unpack("<I", struct.pack("<f", wear_val))[0]
    attrs = [
        {"defindex": 866, "value": 123},
        {"defindex": 867, "value": hi},
    ]
    wear, seed = _decode_seed_info(attrs)
    assert wear == pytest.approx(wear_val)
    assert seed == 123


def test_decode_seed_info_swapped():
    wear_val = 0.3
    lo = struct.unpack("<I", struct.pack("<f", wear_val))[0]
    attrs = [
        {"defindex": 866, "value": lo},
        {"defindex": 867, "value": 456},
    ]
    wear, seed = _decode_seed_info(attrs)
    expected = struct.unpack("<f", struct.pack("<I", 456))[0]
    assert wear == expected
    assert seed == lo


def test_decode_seed_info_attr_classes(monkeypatch):
    monkeypatch.setattr(
        local_data,
        "SCHEMA_ATTRIBUTES",
        {
            866: {"attribute_class": "lo"},
            867: {"attribute_class": "hi"},
            1: {"attribute_class": "lo"},
            2: {"attribute_class": "hi"},
        },
        False,
    )
    wear_val = 0.1
    hi = struct.unpack("<I", struct.pack("<f", wear_val))[0]
    attrs = [
        {"defindex": 1, "value": 789},
        {"defindex": 2, "value": hi},
    ]
    wear, seed = _decode_seed_info(attrs)
    assert wear == pytest.approx(wear_val)
    assert seed == 789
