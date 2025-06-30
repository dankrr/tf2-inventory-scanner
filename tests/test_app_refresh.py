import importlib
import sys


def test_refresh_flag_triggers_update(monkeypatch):
    called = {"hybrid": False}

    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr(
        "utils.schema_manager.load_hybrid_schema",
        lambda force_rebuild=True: called.__setitem__("hybrid", True) or {},
    )
    monkeypatch.setattr("utils.local_data.load_files", lambda: ({}, {}))
    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", lambda: {})
    monkeypatch.setattr(sys, "argv", ["app.py", "--refresh"])
    sys.modules.pop("app", None)
    importlib.import_module("app")
    assert called["hybrid"]
