from translate_and_enrich import enrich_inventory
from utils import inventory_processor as ip
from utils import local_data as ld


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
    icons = {b.get("icon") if isinstance(b, dict) else b for b in item["badges"]}
    assert "›››" in icons
    assert "🖌" in icons
    assert "🎨" in icons


def test_extract_spells_and_badges(monkeypatch):
    ld.ITEMS_BY_DEFINDEX = {501: {"item_name": "Gun", "image_url": ""}}

    monkeypatch.setattr(
        ld,
        "SCHEMA_ATTRIBUTES",
        {
            1009: {
                "name": "SPELL: Halloween ghosts",
                "attribute_class": "halloween_death_ghosts",
            },
            2001: {
                "name": "SPELL: Halloween fire",
                "attribute_class": "halloween_green_flames",
            },
            2000: {
                "name": "SPELL: set Halloween footstep type",
                "attribute_class": "halloween_footstep_type",
            },
            3001: {
                "name": "SPELL: Pumpkin explosions",
                "attribute_class": "halloween_pumpkin_explosions",
            },
            1010: {
                "name": "SPELL: Halloween voice modulation",
                "attribute_class": "halloween_voice_modulation",
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
            "halloween_footstep_type": "Halloween Footprints",
            "halloween_pumpkin_explosions": "Pumpkin Bombs",
            "halloween_voice_modulation": "Voices From Below",
        },
        False,
    )

    asset = {
        "defindex": 501,
        "quality": 6,
        "attributes": [
            {"defindex": 1009},
            {"defindex": 2001},
            {"defindex": 2000},
            {"defindex": 3001},
            {"defindex": 1010},
        ],
    }

    badges, names = ip._extract_spells(asset)
    expected_spells = [
        "Exorcism",
        "Halloween Fire",
        "Halloween Footprints",
        "Pumpkin Bombs",
        "Voices From Below",
    ]
    assert set(names) == set(expected_spells)

    item = ip._process_item(asset)
    icons = {b["icon"] for b in item["badges"]}
    assert {"👻", "🖌", "👣", "🎤", "🎃"} <= icons

    items = ip.enrich_inventory({"items": [asset]})
    assert set(items[0]["modal_spells"]) == set(expected_spells)
