import sys
import main


def test_main_passes_steamid_to_inventory_provider(monkeypatch):
    called = {"id": None}

    class DummyProvider:
        def __init__(self, key):
            pass

        def get_inventory(self, steamid):
            called["id"] = steamid
            return []

    class DummyEnricher:
        def __init__(self, schema):
            pass

        def enrich_inventory(self, items):
            return []

    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr(main, "InventoryProvider", DummyProvider)
    monkeypatch.setattr(main, "ItemEnricher", DummyEnricher)
    monkeypatch.setattr(main, "SchemaProvider", lambda: None)

    monkeypatch.setattr(sys, "argv", ["main.py", "123"])
    main.main()
    assert called["id"] == "123"
