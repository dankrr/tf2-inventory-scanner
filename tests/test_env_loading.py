import importlib
import sys
from pathlib import Path

import pytest


def test_missing_env_vars_raises(monkeypatch):
    monkeypatch.delenv("STEAM_API_KEY", raising=False)
    monkeypatch.setattr("utils.local_data.load_files", lambda *a, **k: ({}, {}))
    sys.modules.pop("app", None)
    with pytest.raises(ValueError):
        importlib.import_module("app")


def test_env_present_allows_import(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BPTF_API_KEY", "x")
    monkeypatch.setattr(
        "utils.price_loader.ensure_prices_cached",
        lambda refresh=False: Path("prices.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached",
        lambda refresh=False: Path("currencies.json"),
    )
    monkeypatch.setattr("utils.price_loader.build_price_map", lambda path: {})
    monkeypatch.setattr(
        "utils.price_loader.PRICE_MAP_FILE",
        Path("price_map.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.dump_price_map",
        lambda mapping, path=Path("price_map.json"): path,
    )
    monkeypatch.setattr("utils.local_data.load_files", lambda *a, **k: ({}, {}))
    sys.modules.pop("app", None)
    importlib.import_module("app")
