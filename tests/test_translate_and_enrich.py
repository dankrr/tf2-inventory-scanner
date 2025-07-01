from translate_and_enrich import enrich_inventory


def test_decorated_flamethrower_enrichment():
    raw = {
        "assets": [
            {
                "classid": "1",
                "instanceid": "0",
                "attributes": [
                    {"defindex": 2025, "value": "3"},
                    {"defindex": 2014, "value": "3"},
                    {"defindex": 2013, "value": "2000"},
                    {"defindex": 142, "value": "3100495"},
                    {"defindex": 725, "float_value": 0.2},
                    {"defindex": 834, "value": "350"},
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
    assert item["sheen"] == "Mandarin"
    assert item["killstreaker"] == "Fire Horns"
    assert item["wear"] == "Field-Tested"
    assert item["paintkit"] == "Warhawk"
    assert "🎯" in item["badges"]
    assert "🖌" in item["badges"]
    assert "🎨" in item["badges"]
