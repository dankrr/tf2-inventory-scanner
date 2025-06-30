import importlib
import sys

import pytest


def test_refresh_flag_triggers_update(monkeypatch):
    called = {"schema": False, "items": False, "hybrid": False}

    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr("pathlib.Path.write_text", lambda self, text: None)
    monkeypatch.setattr(
        "pathlib.Path.mkdir", lambda self, parents=True, exist_ok=True: None
    )
    monkeypatch.setattr(
        "utils.schema_fetcher._fetch_schema",
        lambda k: called.__setitem__("schema", True) or {"items": {}},
    )
    monkeypatch.setattr(
        "utils.items_game_cache.update_items_game",
        lambda: called.__setitem__("items", True) or {},
    )
    monkeypatch.setattr("utils.local_data.clean_items_game", lambda d: {})
    monkeypatch.setattr(
        "utils.schema_manager.build_hybrid_schema",
        lambda: called.__setitem__("hybrid", True) or {},
    )
    monkeypatch.setattr(sys, "argv", ["app.py", "--refresh"])
    sys.modules.pop("app", None)
    with pytest.raises(SystemExit):
        importlib.import_module("app")
    assert all(called.values())
