import pytest
from utils import inventory_processor as ip
from utils import local_data as ld


@pytest.fixture(autouse=True)
def reset_schema(monkeypatch):
    ld.ITEMS_BY_DEFINDEX = {}


def test_enrichment_full_attributes(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 111,
                "quality": 11,
                "attributes": [
                    {"defindex": 2025, "float_value": 3},
                    {"defindex": 2014, "float_value": 3},
                    {"defindex": 2013, "float_value": 2003},
                    {"defindex": 725, "float_value": 0.2},
                    {"defindex": 214, "value": 10},
                    {"defindex": 292, "value": 64},
                    {"defindex": 379, "value": 5},
                    {"defindex": 380, "value": 70},
                    {"defindex": 1009, "value": 1},
                    {"defindex": 1008, "value": 1},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {111: {"item_name": "Rocket Launcher"}}
    ld.QUALITIES_BY_INDEX = {11: "Strange"}
    monkeypatch.setattr(
        ld,
        "SCHEMA_ATTRIBUTES",
        {
            1009: {
                "name": "SPELL: Halloween ghosts",
                "attribute_class": "halloween_death_ghosts",
            },
            1008: {
                "name": "SPELL: Halloween fire",
                "attribute_class": "halloween_green_flames",
            },
        },
        False,
    )
    monkeypatch.setattr(
        ld,
        "SPELL_DISPLAY_NAMES",
        {
            "halloween_death_ghosts": "Exorcism",
            "halloween_green_flames": "Halloween Fire",
        },
        False,
    )
    monkeypatch.setattr(
        ld, "STRANGE_PART_NAMES", {"64": "Kills", "70": "Robots"}, False
    )

    items = ip.enrich_inventory(data)
    item = items[0]

    assert item["killstreak_tier"] == 3
    assert item["killstreak_name"] == "Professional"
    assert item["sheen"] == "Manndarin"
    assert item["killstreak_effect"] == "Cerebral Discharge"
    assert item["wear_name"] == "Field-Tested"
    assert item["strange_count"] == 10
    assert item["score_type"] == "Kills"
    assert set(item["spells"]) == {"Exorcism", "Halloween Fire"}


def test_unknown_values_warn(monkeypatch, caplog):
    caplog.set_level("WARNING")
    data = {
        "items": [
            {
                "defindex": 111,
                "quality": 11,
                "attributes": [
                    {"defindex": 2025, "float_value": 99},
                    {"defindex": 2014, "float_value": 99},
                    {"defindex": 2013, "float_value": 9999},
                    {"defindex": 725, "float_value": 1.5},
                    {"defindex": 214, "value": "bad"},
                    {"defindex": 300, "value": 1},
                    {"defindex": "abc", "value": 2},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {111: {"item_name": "Rocket Launcher"}}
    ld.QUALITIES_BY_INDEX = {11: "Strange"}

    ip.enrich_inventory(data)

    text = caplog.text
    assert "Unknown killstreak tier id" in text
    assert "Unknown sheen id" in text
    assert "Unknown killstreak effect id" in text
    assert "Wear value out of range" in text
