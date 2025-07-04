import importlib
import sys

import pytest


def test_refresh_flag_triggers_update(monkeypatch):
    called = {"schema": False}

    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr("pathlib.Path.write_text", lambda self, text: None)
    monkeypatch.setattr(
        "pathlib.Path.mkdir", lambda self, parents=True, exist_ok=True: None
    )
    monkeypatch.setattr(
        "utils.schema_provider.SchemaProvider.refresh_all",
        lambda self: called.__setitem__("schema", True),
    )
    monkeypatch.setattr(sys, "argv", ["app.py", "--refresh"])
    sys.modules.pop("app", None)
    with pytest.raises(SystemExit):
        importlib.import_module("app")
    assert called["schema"]
