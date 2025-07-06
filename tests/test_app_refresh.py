import importlib
import sys
from pathlib import Path

import pytest


def test_refresh_flag_triggers_update(monkeypatch, capsys):
    called = {"schema": None, "prices": False}

    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BPTF_API_KEY", "x")
    monkeypatch.setattr("pathlib.Path.write_text", lambda self, text: None)
    monkeypatch.setattr(
        "pathlib.Path.mkdir", lambda self, parents=True, exist_ok=True: None
    )

    def fake_refresh(self, verbose: bool = False):
        called["schema"] = verbose
        if verbose:
            print("Fetching items...")
            print("\N{CHECK MARK} Saved cache/schema/items.json (0 entries)")

    monkeypatch.setattr(
        "utils.schema_provider.SchemaProvider.refresh_all", fake_refresh
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_prices_cached",
        lambda refresh=True: called.__setitem__("prices", True) or Path("prices.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached",
        lambda refresh=True: called.__setitem__("curr", True) or Path("curr.json"),
    )
    monkeypatch.setattr(sys, "argv", ["app.py", "--refresh", "--verbose"])
    sys.modules.pop("app", None)
    with pytest.raises(SystemExit):
        importlib.import_module("app")
    out = capsys.readouterr().out
    assert "Fetching items..." in out
    assert "✓ Saved cache/schema/items.json (0 entries)" in out
    assert called["schema"] is True
    assert called["prices"] is True
    assert called["curr"] is True
