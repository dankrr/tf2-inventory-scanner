import importlib
import sys
from pathlib import Path

import pytest


def test_refresh_flag_triggers_update(monkeypatch, capsys):
    called = {"schema": [], "prices": False}

    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BPTF_API_KEY", "x")
    monkeypatch.setattr("pathlib.Path.write_text", lambda self, text: None)
    monkeypatch.setattr(
        "pathlib.Path.mkdir", lambda self, parents=True, exist_ok=True: None
    )

    async def fake_load_schema(self, force: bool = False, language: str = "en"):
        called["schema"].append(force)
        print("\N{CHECK MARK} Saved data/schema_steam.json")

    monkeypatch.setattr(
        "utils.steam_schema.SteamSchemaProvider.load_schema", fake_load_schema
    )

    async def fake_prices_async(refresh=True):
        called["prices"] = True
        return Path("prices.json")

    async def fake_curr_async(refresh=True):
        called["curr"] = True
        return Path("curr.json")

    monkeypatch.setattr(
        "utils.price_loader.ensure_prices_cached",
        lambda refresh=True: called.__setitem__("prices", True) or Path("prices.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached",
        lambda refresh=True: called.__setitem__("curr", True) or Path("curr.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_prices_cached_async",
        fake_prices_async,
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached_async",
        fake_curr_async,
    )
    monkeypatch.setattr(sys, "argv", ["app.py", "--refresh", "--verbose"])
    sys.modules.pop("app", None)
    with pytest.raises(SystemExit):
        importlib.import_module("app")
    out = capsys.readouterr().out
    assert "refetching TF2 schema" in out
    assert "✓ Saved data/schema_steam.json" in out
    assert called["schema"] == [True]
    assert called["prices"] is True
    assert called["curr"] is True
