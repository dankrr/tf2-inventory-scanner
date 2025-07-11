import importlib
import sys
from pathlib import Path

import pytest


def test_missing_env_vars_raises(monkeypatch):
    monkeypatch.delenv("STEAM_API_KEY", raising=False)
    monkeypatch.setattr("utils.local_data.load_files", lambda *a, **k: ({}, {}))
    sys.modules.pop("app", None)
    with pytest.raises(RuntimeError):
        importlib.import_module("app")


def test_env_present_allows_import(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BPTF_API_KEY", "x")
    monkeypatch.setattr(
        "utils.price_loader.ensure_price_map_cached",
        lambda refresh=False: Path("price_map.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached",
        lambda refresh=False: Path("currencies.json"),
    )
    monkeypatch.setattr("utils.price_loader.load_price_map", lambda path: {})
    monkeypatch.setattr("utils.local_data.load_files", lambda *a, **k: ({}, {}))
    sys.modules.pop("app", None)
    importlib.import_module("app")
