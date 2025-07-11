import importlib
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_setup_mode_saves_api_results(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
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

    mod = importlib.import_module("app")
    monkeypatch.setattr(mod.ip, "process_inventory", lambda *a, **k: [])

    calls = {"inv": 0, "sum": 0, "play": 0}

    async def fake_inv(sid):
        calls["inv"] += 1
        return "parsed", {"items": []}

    async def fake_sum(ids):
        calls["sum"] += 1
        return [{"steamid": ids[0], "personaname": "Bob"}]

    async def fake_play(sid):
        calls["play"] += 1
        return 5.0

    monkeypatch.setattr(mod.sac, "fetch_inventory_async", fake_inv)
    monkeypatch.setattr(mod.sac, "get_player_summaries_async", fake_sum)
    monkeypatch.setattr(mod.sac, "get_tf2_playtime_hours_async", fake_play)
    monkeypatch.setattr("builtins.input", lambda *a: "1")

    mod.TEST_MODE = True
    await mod._setup_test_mode()
    assert calls == {"inv": 1, "sum": 1, "play": 1}

    api_dir = Path("cached_inventories") / "1" / "api_results"
    assert (api_dir / "inventory.json").exists()
    assert (api_dir / "player_summaries.json").exists()
    assert (api_dir / "playtime.json").exists()

    # subsequent call should reuse cached files
    monkeypatch.setattr(
        mod.sac,
        "get_player_summaries_async",
        lambda *_: (_ for _ in ()).throw(AssertionError),
    )
    monkeypatch.setattr(
        mod.sac,
        "get_tf2_playtime_hours_async",
        lambda *_: (_ for _ in ()).throw(AssertionError),
    )
    summary = await mod.get_player_summary("1")
    assert summary["username"] == "Bob"
