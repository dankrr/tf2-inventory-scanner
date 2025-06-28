import importlib
import sys

import pytest


def test_missing_env_vars_raises(monkeypatch):
    monkeypatch.delenv("STEAM_API_KEY", raising=False)
    monkeypatch.delenv("BACKPACK_API_KEY", raising=False)
    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", lambda: {})
    sys.modules.pop("app", None)
    with pytest.raises(RuntimeError):
        importlib.import_module("app")


def test_env_present_allows_import(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BACKPACK_API_KEY", "y")
    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", lambda: {})
    sys.modules.pop("app", None)
    importlib.import_module("app")
