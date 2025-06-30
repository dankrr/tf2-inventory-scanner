import json
from utils import schema_manager, inventory_processor


def test_icons_valid(tmp_path, monkeypatch):
    schema = {
        "items": {
            "1": {
                "defindex": 1,
                "name": "One",
                "image": "https://steamcdn-a.akamaihd.net/apps/440/icons/a.png",
            },
            "2": {
                "defindex": 2,
                "name": "Two",
                "image": "https://steamcdn-a.akamaihd.net/apps/440/icons/b.png",
            },
        },
        "qualities": {},
    }
    cache = tmp_path / "hybrid_schema.json"
    cache.write_text(json.dumps(schema))
    monkeypatch.setattr(schema_manager, "HYBRID_FILE", cache)
    monkeypatch.setattr(schema_manager, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(inventory_processor, "HYBRID_SCHEMA", None)

    data = {"items": [{"defindex": 1}, {"defindex": 2}]}
    items = inventory_processor.process_inventory(data)
    assert all(
        i["image_url"].startswith("https://steamcdn-a.akamaihd.net") for i in items
    )
