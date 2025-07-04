import importlib
import sys

import pytest


def test_refresh_flag_triggers_update(monkeypatch, capsys):
    called = {"schema": None}

    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr("pathlib.Path.write_text", lambda self, text: None)
    monkeypatch.setattr(
        "pathlib.Path.mkdir", lambda self, parents=True, exist_ok=True: None
    )

    def fake_refresh(self, verbose: bool = False):
        called["schema"] = verbose
        if verbose:
            print("cache/schema/items.json - 0 entries")

    monkeypatch.setattr(
        "utils.schema_provider.SchemaProvider.refresh_all", fake_refresh
    )
    monkeypatch.setattr(sys, "argv", ["app.py", "--refresh"])
    sys.modules.pop("app", None)
    with pytest.raises(SystemExit):
        importlib.import_module("app")
    out = capsys.readouterr().out
    assert "cache/schema/items.json - 0 entries" in out
    assert called["schema"] is True
