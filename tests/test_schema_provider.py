import utils.schema_provider as sp


class DummyResp:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_schema_provider(monkeypatch, tmp_path):
    provider = sp.SchemaProvider(base_url="https://example.com", cache_dir=tmp_path)

    payloads = {
        "/raw/schema/items": {"5021": {"item_name": "Key"}},
        "/attributes": {"2025": {"name": "Killstreak Tier"}},
        "/effects": {"Burning Flames": {"id": 13, "name": "Burning Flames"}},
        "/paints": {"A Color Similar to Slate": 3100495},
        "/origins": {"0": "Timed Drop"},
        "/parts": {"Kills": {"id": 64, "name": "Kills"}},
        "/qualities": {"Normal": 0},
        "/properties/defindexes": {"5021": "Key"},
    }
    calls = {key: 0 for key in payloads}

    def fake_get(self, url, timeout=20):
        endpoint = url.replace(provider.base_url, "")
        calls[endpoint] += 1
        return DummyResp(payloads[endpoint])

    monkeypatch.setattr(sp.requests.Session, "get", fake_get)

    assert provider.get_items() == {5021: {"item_name": "Key"}}
    assert provider.get_item_by_defindex(5021) == {"item_name": "Key"}
    assert provider.get_attributes() == {2025: {"name": "Killstreak Tier"}}
    assert provider.get_effects() == {13: {"id": 13, "name": "Burning Flames"}}
    assert provider.get_paints() == {"A Color Similar to Slate": 3100495}
    assert provider.get_origins() == {0: "Timed Drop"}
    assert provider.get_parts() == {64: {"id": 64, "name": "Kills"}}
    assert provider.get_qualities() == {"Normal": 0}
    assert provider.get_defindexes() == {5021: "Key"}

    # second calls should hit cache and not increase call counts
    provider.get_items()
    provider.get_attributes()
    provider.get_effects()
    provider.get_paints()
    provider.get_origins()
    provider.get_parts()
    provider.get_qualities()

    for endpoint in payloads:
        assert calls[endpoint] == 1


def test_schema_provider_list_payload(monkeypatch, tmp_path):
    provider = sp.SchemaProvider(base_url="https://example.com", cache_dir=tmp_path)

    payloads = {
        "/raw/schema/items": {"value": [{"defindex": 5021, "item_name": "Key"}]},
        "/attributes": {"value": [{"defindex": 2025, "name": "Killstreak Tier"}]},
        "/effects": {"value": [{"id": 13, "name": "Burning Flames"}]},
        "/paints": {"value": [{"id": 3100495, "name": "A Color Similar to Slate"}]},
        "/origins": {"value": [{"id": 0, "name": "Timed Drop"}]},
        "/parts": {"value": [{"id": 64, "name": "Kills"}]},
        "/qualities": {"value": [{"id": 0, "name": "Normal"}]},
    }

    def fake_get(self, url, timeout=20):
        endpoint = url.replace(provider.base_url, "")
        return DummyResp(payloads[endpoint])

    monkeypatch.setattr(sp.requests.Session, "get", fake_get)

    assert provider.get_items() == {5021: {"defindex": 5021, "item_name": "Key"}}
    assert provider.get_attributes() == {
        2025: {"defindex": 2025, "name": "Killstreak Tier"}
    }
    assert provider.get_effects() == {13: {"id": 13, "name": "Burning Flames"}}
    assert provider.get_paints() == {"A Color Similar to Slate": 3100495}
    assert provider.get_origins() == {0: "Timed Drop"}
    assert provider.get_parts() == {64: {"id": 64, "name": "Kills"}}
    assert provider.get_qualities() == {"Normal": 0}
