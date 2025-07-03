from translate_and_enrich import enrich_inventory
from utils import inventory_processor as ip
from utils import schema_fetcher as sf
from utils import local_data as ld
from utils import items_game_cache as ig


def test_decorated_flamethrower_enrichment():
    raw = {
        "assets": [
            {
                "classid": "1",
                "instanceid": "0",
                "attributes": [
                    {"defindex": 2025, "value": "3"},
                    {"defindex": 2014, "value": "3"},
                    {"defindex": 2013, "value": "2002"},
                    {"defindex": 142, "value": "3100495"},
                    {"defindex": 834, "value": "350"},
                    {"defindex": 866, "value": "123"},
                    {"defindex": 867, "value": "1045220557"},
                    {"defindex": 725, "float_value": 0.2},
                ],
            }
        ],
        "descriptions": [
            {
                "classid": "1",
                "instanceid": "0",
                "app_data": {"def_index": "15141", "quality": "15"},
                "tradable": 1,
                "marketable": 1,
            }
        ],
    }
    maps = {
        "paint_names": {"3100495": "A Color Similar to Slate"},
        "paintkit_names": {"350": "Warhawk"},
    }
    item = enrich_inventory(
        raw,
        {"15141": {"item_name": "Flamethrower"}},
        {"15141": {"name": "Flamethrower"}},
        maps,
    )[0]

    assert item["quality"] == "Decorated Weapon"
    assert item["killstreak_tier"] == "Professional Killstreak"
    assert item["sheen"] == "Manndarin"
    assert item["killstreaker"] == "Fire Horns"
    assert item["wear"] == "Field-Tested"
    assert item["paintkit"] == "Warhawk"
    assert item["pattern_seed"] == 123
    assert "🎯" in item["badges"]
    assert "🖌" in item["badges"]
    assert "🎨" in item["badges"]


def test_extract_spells_and_badges(monkeypatch):
    sf.SCHEMA = {"501": {"defindex": 501, "item_name": "Gun", "image_url": ""}}
    ld.TF2_SCHEMA = {}
    ld.ITEMS_GAME_CLEANED = {}
    monkeypatch.setattr(ig, "ensure_items_game_cached", lambda: {})
    monkeypatch.setattr(ig, "ITEM_BY_DEFINDEX", {}, False)

    asset = {
        "defindex": 501,
        "quality": 6,
        "attributes": [],
        "descriptions": [
            {"value": "Halloween: Exorcism (spell only active during event)"},
            {"value": "Paint Spell: Chromatic Corruption"},
            {"value": "Halloween: Team Spirit Footprints"},
            {"value": "Halloween: Pumpkin Bombs"},
            {"value": "Rare Spell: Voices From Below"},
        ],
    }

    spells, flags = ip._extract_spells(asset)
    expected_spells = [
        "Exorcism",
        "Chromatic Corruption",
        "Team Spirit Footprints",
        "Pumpkin Bombs",
        "Voices From Below",
    ]
    assert spells == expected_spells
    assert flags == {
        "has_exorcism": True,
        "has_paint_spell": True,
        "has_footprints": True,
        "has_pumpkin_bombs": True,
        "has_voice_lines": True,
    }

    item = ip._process_item(asset, sf.SCHEMA, {})
    icons = {b["icon"] for b in item["badges"]}
    assert {"👻", "🫟", "👣", "🗣️"} <= icons

    items = ip.enrich_inventory({"items": [asset]})
    assert items[0]["modal_spells"] == expected_spells
