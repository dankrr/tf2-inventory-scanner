import utils.schema_provider as sp


class DummyResp:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_schema_provider(monkeypatch):
    provider = sp.SchemaProvider(base_url="https://example.com")

    payloads = {
        "/properties/effects": {"Burning Flames": 13},
        "/properties/paints": {"A Color Similar to Slate": 3100495},
        "/properties/paintkits": {"Warhawk": 350},
        "/properties/killstreaks": {"1": "Alpha"},
        "/properties/wears": {"0": "Factory New"},
        "/properties/qualities": {"Normal": 0},
        "/properties/defindexes": {"5021": "Key"},
        "/properties/crateseries": {"1": "100"},
        "/properties/strangeParts": {"Kills": "64"},
        "/properties/craftWeapons": ["1101;foo"],
        "/properties/uncraftWeapons": ["2202;bar"],
    }
    calls = {key: 0 for key in payloads}

    def fake_get(self, url, timeout=20):
        endpoint = url.replace(provider.base_url, "")
        calls[endpoint] += 1
        return DummyResp(payloads[endpoint])

    monkeypatch.setattr(sp.requests.Session, "get", fake_get)

    assert provider.get_effects() == {13: "Burning Flames"}
    assert provider.get_paints() == {3100495: "A Color Similar to Slate"}
    assert provider.get_paintkits() == {350: "Warhawk"}
    assert provider.get_killstreaks() == {1: "Alpha"}
    assert provider.get_wears() == {0: "Factory New"}
    assert provider.get_qualities() == {0: "Normal"}
    assert provider.get_defindexes() == {5021: "Key"}
    assert provider.get_crateseries() == {1: 100}
    assert provider.get_strangeParts() == {"64": "Kills"}
    assert provider.get_craftWeapons() == {1101: "1101;foo"}
    assert provider.get_uncraftWeapons() == {2202: "2202;bar"}

    # second calls should hit cache and not increase call counts
    provider.get_effects()
    provider.get_paints()
    provider.get_paintkits()
    provider.get_killstreaks()
    provider.get_wears()
    provider.get_qualities()
    provider.get_defindexes()
    provider.get_crateseries()
    provider.get_strangeParts()
    provider.get_craftWeapons()
    provider.get_uncraftWeapons()

    for endpoint in payloads:
        assert calls[endpoint] == 1
