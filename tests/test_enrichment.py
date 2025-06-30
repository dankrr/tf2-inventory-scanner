import json

from utils import schema_manager, inventory_processor


def test_full_enrichment(tmp_path, monkeypatch):
    schema = {
        "items": {
            "199": {
                "name": "The Revolver",
                "item_type_name": "Pistol",
                "image_url": "img.png",
            }
        },
        "qualities": {"11": "Strange"},
        "qualityNames": {"strange": "#CF6A32"},
        "effects": {"2003": "Incinerator"},
        "paint_kits": {},
        "strange_parts": {"24": "Players Hit"},
    }
    cache = tmp_path / "hybrid_schema.json"
    cache.write_text(json.dumps(schema))
    monkeypatch.setattr(schema_manager, "HYBRID_FILE", cache)
    monkeypatch.setattr(schema_manager, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(inventory_processor, "HYBRID_SCHEMA", None)

    data = {
        "items": [
            {
                "defindex": 199,
                "quality": 11,
                "custom_name": "My Trusty Sidearm",
                "level": 42,
                "origin": 5,
                "attributes": [
                    {"defindex": 2014, "value": 3},
                    {"defindex": 2012, "value": 2},
                    {"defindex": 2013, "value": 2003},
                    {"defindex": 2053, "value": 1},
                    {"defindex": 382, "value": 24},
                ],
            }
        ]
    }

    items = inventory_processor.enrich_inventory(data)
    assert items[0]["base_name"] == "The Revolver"
    assert items[0]["name"] == "My Trusty Sidearm"
    assert items[0]["killstreak_tier"] == "Professional"
    assert items[0]["sheen"] == "Deadly Daffodil"
    assert items[0]["killstreaker"] == "Incinerator"
    assert items[0]["is_festivized"] is True
    assert items[0]["strange_parts"] == ["Players Hit"]
    for badge in ["\u2694\ufe0f", "\u2728", "\U0001f480", "\U0001f384", "\U0001f4ca"]:
        assert badge in items[0]["badges"]
