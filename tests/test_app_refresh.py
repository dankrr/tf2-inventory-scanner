import importlib
import sys

import pytest


def test_refresh_flag_triggers_update(monkeypatch):
    called = {"schema": False, "items": False}

    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr("pathlib.Path.write_text", lambda self, text: None)
    monkeypatch.setattr(
        "pathlib.Path.mkdir", lambda self, parents=True, exist_ok=True: None
    )
    monkeypatch.setattr(
        "utils.schema_fetcher.refresh_schema",
        lambda: called.__setitem__("schema", True) or {"1": {}},
    )
    monkeypatch.setattr(
        "utils.items_game_cache.load_items_game_cleaned",
        lambda force_rebuild=False: called.__setitem__("items", force_rebuild)
        or {"1": {}},
    )
    monkeypatch.setattr(sys, "argv", ["app.py", "--refresh"])
    sys.modules.pop("app", None)
    with pytest.raises(SystemExit):
        importlib.import_module("app")
    assert called["schema"] and called["items"]
