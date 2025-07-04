from utils.item_enricher import ItemEnricher, _decode_float_bits_to_int
from utils.schema_provider import SchemaProvider
import struct


def test_enrich_inventory(monkeypatch):
    provider = SchemaProvider(base_url="https://example.com")

    monkeypatch.setattr(
        provider, "get_items", lambda: {100: {"defindex": 100, "item_name": "Rocket"}}
    )
    monkeypatch.setattr(provider, "get_qualities", lambda: {"Unique": 6})
    monkeypatch.setattr(provider, "get_paints", lambda: {"Team Spirit": 1})
    monkeypatch.setattr(
        provider,
        "get_attributes",
        lambda: {
            142: {"defindex": 142, "class": "set_item_tint_rgb"},
            2025: {"defindex": 2025, "name": "killstreak tier"},
            2013: {"defindex": 2013, "name": "killstreak sheen"},
            2014: {"defindex": 2014, "name": "killstreak effect"},
            134: {"defindex": 134, "class": "set_attached_particle"},
            5000: {"defindex": 5000},
        },
    )
    monkeypatch.setattr(provider, "get_effects", lambda: {55: "Hot"})
    monkeypatch.setattr(provider, "get_strange_parts", lambda: {5000: "Kills"})

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
    assert item["killstreak_tier"] == "Specialized Killstreak"
    assert item["sheen"] == "Hot"
    assert item["killstreaker"] == "Hot"
    assert item["unusual_effect"] == "Hot"
    assert item["strange_parts"] == ["Kills"]


def test_spell_extraction(monkeypatch):
    provider = SchemaProvider(base_url="https://example.com")

    monkeypatch.setattr(
        provider, "get_items", lambda: {1: {"defindex": 1, "item_name": "Hat"}}
    )
    monkeypatch.setattr(provider, "get_qualities", lambda: {"Unique": 6})
    monkeypatch.setattr(provider, "get_paints", lambda: {})
    monkeypatch.setattr(
        provider,
        "get_attributes",
        lambda: {
            8901: {
                "defindex": 8901,
                "name": "SPELL: Die Job",
                "attribute_class": "set_item_tint_rgb_override",
            },
            8902: {
                "defindex": 8902,
                "description_string": "#Attrib_Halloween_Footstep_Type",
            },
            8903: {"defindex": 8903, "name": "SPELL: Halloween voice modulation"},
        },
    )
    monkeypatch.setattr(provider, "get_effects", lambda: {})
    monkeypatch.setattr(provider, "get_strange_parts", lambda: {})

    enricher = ItemEnricher(provider)

    def enc(i: int) -> float:
        return struct.unpack("<f", struct.pack("<I", i))[0]

    raw = [
        {
            "defindex": 1,
            "quality": 6,
            "attributes": [
                {"defindex": 8901, "float_value": enc(3)},
                {"defindex": 8902, "value": 2},
                {"defindex": 8903, "float_value": enc(1)},
            ],
        }
    ]

    item = enricher.enrich_inventory(raw)[0]
    spells = item["spells"]

    assert {"name": "Die Job", "type": "paint", "count": 3} in spells
    assert {
        "name": "Halloween Footstep Type",
        "type": "footprint",
        "count": 2,
    } in spells
    assert {
        "name": "Halloween voice modulation",
        "type": "voices",
        "count": 1,
    } in spells


def test_decode_float_bits_to_int():
    val = struct.unpack("<f", struct.pack("<I", 7))[0]
    assert _decode_float_bits_to_int(val) == 7
