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
        "/raw/schema/attributes": {"2025": {"name": "Killstreak Tier"}},
        "/properties/effects": {"Burning Flames": {"id": 13, "name": "Burning Flames"}},
        "/properties/paints": {"A Color Similar to Slate": 3100495},
        "/raw/schema/originNames": {"0": "Timed Drop"},
        "/properties/strangeParts": {"Kills": {"id": 64, "name": "Kills"}},
        "/properties/qualities": {"Normal": 0},
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
        "/raw/schema/attributes": {
            "value": [{"defindex": 2025, "name": "Killstreak Tier"}]
        },
        "/properties/effects": {"value": [{"id": 13, "name": "Burning Flames"}]},
        "/properties/paints": {
            "value": [{"id": 3100495, "name": "A Color Similar to Slate"}]
        },
        "/raw/schema/originNames": {"value": [{"id": 0, "name": "Timed Drop"}]},
        "/properties/strangeParts": {"value": [{"id": 64, "name": "Kills"}]},
        "/properties/qualities": {"value": [{"id": 0, "name": "Normal"}]},
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


def test_refresh_all_resets_attributes_and_creates_files(monkeypatch, tmp_path):
    provider = sp.SchemaProvider(base_url="https://example.com", cache_dir=tmp_path)

    monkeypatch.setattr(
        sp.requests.Session,
        "get",
        lambda self, url, timeout=20: DummyResp({}),
    )

    provider.items_by_defindex = {}
    provider.attributes_by_defindex = {}
    provider.paints_map = {}
    provider.parts_by_defindex = {}
    provider.defindex_names = {}
    provider.qualities_map = {}
    provider.effects_by_index = {}
    provider.origins_by_index = {}

    logs: list[str] = []
    monkeypatch.setattr(provider._logger, "info", lambda msg, *a: logs.append(msg % a))

    provider.refresh_all(verbose=True)

    for key in provider.ENDPOINTS:
        assert (tmp_path / f"{key}.json").exists()

    assert provider.items_by_defindex is None
    assert provider.attributes_by_defindex is None
    assert provider.paints_map is None
    assert provider.parts_by_defindex is None
    assert provider.defindex_names is None
    assert provider.qualities_map is None
    assert provider.effects_by_index is None
    assert provider.origins_by_index is None

    for key in provider.ENDPOINTS:
        fname = f"{tmp_path / key}.json"
        assert any(fname in msg for msg in logs)
