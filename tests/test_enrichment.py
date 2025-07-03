import pytest
from utils import inventory_processor as ip
from utils import schema_fetcher as sf
from utils import items_game_cache as ig
from utils import local_data as ld


@pytest.fixture(autouse=True)
def no_items_game(monkeypatch):
    monkeypatch.setattr(ig, "ensure_items_game_cached", lambda: {})
    monkeypatch.setattr(ig, "ITEM_BY_DEFINDEX", {}, False)
    ld.TF2_SCHEMA = {}
    ld.ITEMS_GAME_CLEANED = {}


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
                    {"defindex": 2001, "value": 3},
                ],
            }
        ]
    }
    sf.SCHEMA = {"111": {"defindex": 111, "item_name": "Rocket Launcher"}}
    sf.QUALITIES = {"11": "Strange"}
    monkeypatch.setattr(
        ld, "STRANGE_PART_NAMES", {"64": "Kills", "70": "Robots"}, False
    )

    items = ip.enrich_inventory(data)
    item = items[0]

    assert item["killstreak_tier"] == "Professional Killstreak"
    assert item["sheen"] == "Manndarin"
    assert item["killstreak_effect"] == "Cerebral Discharge"
    assert item["wear_name"] == "Field-Tested"
    assert item["strange_count"] == 10
    assert item["score_type"] == "Kills"
    assert set(item["spells"]) == {"Exorcism", "Chromatic Corruption"}


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
    sf.SCHEMA = {"111": {"defindex": 111, "item_name": "Rocket Launcher"}}
    sf.QUALITIES = {"11": "Strange"}

    ip.enrich_inventory(data)

    text = caplog.text
    assert "Unknown killstreak tier id" in text
    assert "Unknown sheen id" in text
    assert "Unknown killstreak effect id" in text
    assert "Wear value out of range" in text
    assert "Invalid kill-eater value" in text
    assert "Unknown kill-eater index" in text
    assert "Invalid kill-eater defindex" in text
