import sys
from pathlib import Path
import importlib
import asyncio

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def app(monkeypatch):
    """Return Flask app with env and schema mocks."""

    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", lambda: {})
    monkeypatch.setattr("utils.local_data.load_files", lambda: ({}, {}))
    monkeypatch.setattr(
        "utils.items_game_cache.ensure_future",
        lambda *a, **k: asyncio.get_event_loop().create_future(),
    )

    mod = importlib.import_module("app")
    importlib.reload(mod)
    mod.app.secret_key = "test"
    return mod.app
