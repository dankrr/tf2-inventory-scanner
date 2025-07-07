from utils.item_enricher import ItemEnricher, _decode_float_bits_to_int
from utils.schema_provider import SchemaProvider
from utils import inventory_processor as ip, local_data as ld
from utils.valuation_service import ValuationService
import pytest
import struct


@pytest.fixture(autouse=True)
def reset_data():
    ld.ITEMS_BY_DEFINDEX = {}
    ld.SCHEMA_ATTRIBUTES = {}


@pytest.fixture
def patch_valuation(monkeypatch):
    def _apply(price_map):
        service = ValuationService(price_map=price_map)
        monkeypatch.setattr(ip, "get_valuation_service", lambda: service)
        return service

    return _apply


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


def test_enrich_inventory_attribute_class(monkeypatch):
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
            142: {"defindex": 142, "attribute_class": "set_item_tint_rgb"},
            134: {"defindex": 134, "attribute_class": "set_attached_particle"},
        },
    )
    monkeypatch.setattr(provider, "get_effects", lambda: {55: "Hot"})
    monkeypatch.setattr(provider, "get_strange_parts", lambda: {})

    enricher = ItemEnricher(provider)

    raw = [
        {
            "defindex": 100,
            "quality": 6,
            "attributes": [
                {"defindex": 142, "value": 1},
                {"defindex": 134, "value": 55},
            ],
        }
    ]

    item = enricher.enrich_inventory(raw)[0]
    assert item["paint"] == "Team Spirit"
    assert item["unusual_effect"] == "Hot"


def test_enrich_inventory_attribute_class_2041(monkeypatch):
    provider = SchemaProvider(base_url="https://example.com")

    monkeypatch.setattr(
        provider, "get_items", lambda: {100: {"defindex": 100, "item_name": "Rocket"}}
    )
    monkeypatch.setattr(provider, "get_qualities", lambda: {"Unique": 6})
    monkeypatch.setattr(provider, "get_paints", lambda: {})
    monkeypatch.setattr(
        provider,
        "get_attributes",
        lambda: {2041: {"defindex": 2041, "attribute_class": "set_attached_particle"}},
    )
    monkeypatch.setattr(provider, "get_effects", lambda: {55: "Hot"})
    monkeypatch.setattr(provider, "get_strange_parts", lambda: {})

    enricher = ItemEnricher(provider)

    raw = [
        {"defindex": 100, "quality": 6, "attributes": [{"defindex": 2041, "value": 55}]}
    ]

    item = enricher.enrich_inventory(raw)[0]
    assert item["unusual_effect"] == "Hot"


def test_spell_extraction(monkeypatch):
    provider = SchemaProvider(base_url="https://example.com")

    monkeypatch.setattr(
        provider, "get_items", lambda: {1: {"defindex": 1, "item_name": "Hat"}}
    )
    monkeypatch.setattr(provider, "get_qualities", lambda: {"Unique": 6})
    monkeypatch.setattr(provider, "get_paints", lambda: {})
    monkeypatch.setattr(provider, "get_attributes", lambda: {})
    monkeypatch.setattr(provider, "get_effects", lambda: {})
    monkeypatch.setattr(provider, "get_strange_parts", lambda: {})

    enricher = ItemEnricher(provider)

    raw = [
        {
            "defindex": 1,
            "quality": 6,
            "attributes": [
                {"defindex": 1004, "float_value": 0},
                {"defindex": 1005, "value": 1},
                {"defindex": 1006, "float_value": 1},
            ],
        }
    ]

    item = enricher.enrich_inventory(raw)[0]
    spells = item["spells"]

    assert "Die Job" in spells
    assert "Team Spirit Footprints" in spells
    assert "Voices From Below" in spells


def test_decode_float_bits_to_int():
    val = struct.unpack("<f", struct.pack("<I", 7))[0]
    assert _decode_float_bits_to_int(val) == 7


def test_price_lookup_cosmetic_effect(patch_valuation):
    asset = {
        "defindex": 5001,
        "quality": 5,
        "attributes": [{"defindex": 134, "float_value": 55}],
    }
    ld.ITEMS_BY_DEFINDEX = {5001: {"item_name": "Cool Hat", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {5: "Unusual"}
    price_map = {
        ("Cool Hat", 5, False, 55, 0): {"value_raw": 50.0, "currency": "metal"}
    }
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}
    patch_valuation(price_map)
    item = ip.enrich_inventory({"items": [asset]})[0]
    assert item["price"] == price_map[("Cool Hat", 5, False, 55, 0)]
    assert item["price_string"] == "1 Key"


def test_price_lookup_taunt_effect(patch_valuation):
    asset = {
        "defindex": 6001,
        "quality": 5,
        "attributes": [{"defindex": 134, "float_value": 54}],
    }
    ld.ITEMS_BY_DEFINDEX = {6001: {"item_name": "Taunt: Conga", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {5: "Unusual"}
    price_map = {
        ("Taunt: Conga", 5, False, 54, 0): {"value_raw": 100.0, "currency": "metal"}
    }
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}
    patch_valuation(price_map)
    item = ip.enrich_inventory({"items": [asset]})[0]
    assert item["price"] == price_map[("Taunt: Conga", 5, False, 54, 0)]
    assert item["price_string"] == "2 Keys"
