import sys
from pathlib import Path
import importlib

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def app(monkeypatch):
    """Return Flask app with env and schema mocks."""

    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BPTF_API_KEY", "x")
    monkeypatch.setattr("utils.local_data.load_files", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(
        "utils.price_loader.ensure_price_map_cached",
        lambda refresh=False: Path("price_map.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached",
        lambda refresh=False: Path("currencies.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.load_price_map",
        lambda path: {},
    )

    mod = importlib.import_module("app")
    importlib.reload(mod)
    mod.app.secret_key = "test"
    return mod.app
