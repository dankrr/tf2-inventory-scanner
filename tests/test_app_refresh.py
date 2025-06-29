import importlib
import sys

import pytest


def test_refresh_flag_triggers_update(monkeypatch):
    called = {"autobot": False}

    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr("pathlib.Path.write_text", lambda self, text: None)
    monkeypatch.setattr(
        "pathlib.Path.mkdir", lambda self, parents=True, exist_ok=True: None
    )

    def fake_cache(refresh=False):
        called["autobot"] = refresh

    monkeypatch.setattr(
        "utils.autobot_schema_cache.ensure_all_cached",
        fake_cache,
    )
    monkeypatch.setattr("utils.local_data.load_files", lambda: None)
    monkeypatch.setattr(sys, "argv", ["app.py", "--refresh"])
    sys.modules.pop("app", None)
    with pytest.raises(SystemExit):
        importlib.import_module("app")
    assert called["autobot"]
