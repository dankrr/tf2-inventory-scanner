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
    monkeypatch.setattr(
        "utils.price_loader.build_price_map",
        lambda path: {},
    )

    mod = importlib.import_module("app")
    importlib.reload(mod)
    mod.app.secret_key = "test"
    return mod.app


class AsyncTestClient:
    def __init__(self, client):
        self._client = client

    async def get(self, *args, **kwargs):
        return await asyncio.to_thread(self._client.get, *args, **kwargs)

    async def post(self, *args, **kwargs):
        return await asyncio.to_thread(self._client.post, *args, **kwargs)


@pytest.fixture
def async_client(app):
    return AsyncTestClient(app.test_client())
