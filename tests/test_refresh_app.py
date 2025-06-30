import importlib
import sys


def test_refresh_argument_triggers_refresh(monkeypatch):
    called = {}

    def fake_refresh():
        called["done"] = True

    monkeypatch.setattr("scripts.fetch_data.refresh_all", fake_refresh)
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", lambda: {})

    sys.modules.pop("app", None)
    sys.argv.append("--refresh")
    importlib.import_module("app")
    sys.argv.remove("--refresh")

    assert called.get("done") is True
