import importlib
import sys
from pathlib import Path

import pytest


def _mock_app_import(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BPTF_API_KEY", "x")
    monkeypatch.setattr("utils.local_data.load_files", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(
        "utils.price_loader.ensure_prices_cached",
        lambda refresh=False: Path("prices.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached",
        lambda refresh=False: Path("currencies.json"),
    )
    monkeypatch.setattr("utils.price_loader.build_price_map", lambda path: {})
    monkeypatch.setattr("utils.price_loader.PRICE_MAP_FILE", Path("price_map.json"))
    monkeypatch.setattr(
        "utils.price_loader.dump_price_map",
        lambda mapping, path=Path("price_map.json"): path,
    )

    async def fake_fetch(*a, **k):
        return True, False, False

    monkeypatch.setattr("utils.cache_manager.fetch_missing_cache_files", fake_fetch)
    sys.modules.pop("app", None)
    sys.modules.pop("run", None)
    sys.modules.pop("app", None)
    sys.modules.pop("app", None)
    return importlib.import_module("run")


@pytest.mark.asyncio
async def test_main_kills_and_serves(monkeypatch):
    called = {"kill": False, "serve": False}

    monkeypatch.setenv("PORT", "1234")
    run = _mock_app_import(monkeypatch)

    monkeypatch.setattr(
        run, "kill_process_on_port", lambda p: called.__setitem__("kill", p)
    )

    async def fake_serve(app, config):
        called["serve"] = config.bind[0]

    monkeypatch.setattr(run, "serve", fake_serve)

    await run.main()

    assert called["kill"] == 1234
    assert called["serve"] == "0.0.0.0:1234"


@pytest.mark.asyncio
async def test_main_test_mode_calls_setup(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["run.py", "--test"])
    called = {"setup": False}

    mod = _mock_app_import(monkeypatch)

    async def fake_setup():
        called["setup"] = True

    monkeypatch.setattr(mod, "_setup_test_mode", fake_setup)

    async def fake_serve(app, config):
        pass

    monkeypatch.setattr(mod, "serve", fake_serve)

    await mod.main()

    assert called["setup"] is True


def test_refresh_flag_triggers_update(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["run.py", "--refresh", "--verbose"])
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

    async def fake_refresh_async():
        fake_refresh(None, True)
        await fake_prices_async()
        await fake_curr_async()

    monkeypatch.setattr("utils.cache_manager._do_refresh", fake_refresh_async)

    monkeypatch.setattr(
        "utils.price_loader.ensure_prices_cached",
        lambda refresh=True: called.__setitem__("prices", True) or Path("prices.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached",
        lambda refresh=True: called.__setitem__("curr", True) or Path("curr.json"),
    )

    async def fake_prices_async(refresh=True):
        called["prices"] = True
        return Path("prices.json")

    async def fake_curr_async(refresh=True):
        called["curr"] = True
        return Path("curr.json")

    monkeypatch.setattr(
        "utils.price_loader.ensure_prices_cached_async",
        fake_prices_async,
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached_async",
        fake_curr_async,
    )
    monkeypatch.setattr("utils.cache_manager._save_json_atomic", lambda *a, **k: None)

    sys.modules.pop("run", None)
    sys.modules.pop("app", None)
    exited = False
    try:
        importlib.import_module("run")
    except SystemExit:
        exited = True
    assert exited is True
    out = capsys.readouterr().out
    assert "Fetching items..." in out
    assert "✓ Saved cache/schema/items.json (0 entries)" in out
    assert called["schema"] is True
    assert called["prices"] is True
