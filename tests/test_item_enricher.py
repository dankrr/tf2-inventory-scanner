from utils.item_enricher import ItemEnricher
from utils.schema_provider import SchemaProvider


def test_enrich_inventory(monkeypatch):
    provider = SchemaProvider(base_url="https://example.com")

    monkeypatch.setattr(provider, "get_defindexes", lambda: {100: "Rocket"})
    monkeypatch.setattr(provider, "get_qualities", lambda: {6: "Unique"})
    monkeypatch.setattr(provider, "get_paints", lambda: {1: "Team Spirit"})
    monkeypatch.setattr(provider, "get_killstreaks", lambda: {2: "Specialized"})
    monkeypatch.setattr(provider, "get_effects", lambda: {55: "Hot"})
    monkeypatch.setattr(provider, "get_paintkits", lambda: {3: "Warhawk"})
    monkeypatch.setattr(provider, "get_strangeParts", lambda: {"5000": "Kills"})

    enricher = ItemEnricher(provider)

    raw = [
        {
            "id": "1",
            "defindex": 100,
            "original_id": "1",
            "inventory": 123,
            "quality": 6,
            "attributes": [
                {"defindex": 142, "value": 1},
                {"defindex": 2025, "value": 2},
                {"defindex": 2013, "value": 55},
                {"defindex": 2014, "value": 55},
                {"defindex": 134, "value": 55},
                {"defindex": 834, "value": 3},
                {"defindex": 5000, "value": 1},
            ],
        }
    ]

    items = enricher.enrich_inventory(raw)
    item = items[0]
    assert item["name"] == "Rocket"
    assert item["quality"] == "Unique"
    assert item["paint"] == "Team Spirit"
    assert item["killstreak_tier"] == "Specialized"
    assert item["sheen"] == "Hot"
    assert item["killstreaker"] == "Hot"
    assert item["unusual_effect"] == "Hot"
    assert item["paintkit"] == "Warhawk"
    assert item["strange_parts"] == ["Kills"]
