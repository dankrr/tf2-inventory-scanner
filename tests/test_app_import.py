import importlib
import asyncio


def test_app_uses_mock_schema(monkeypatch):
    mock_schema = {"5": {"defindex": 5, "name": "Five"}}

    def fake_ensure():
        return mock_schema

    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", fake_ensure)
    monkeypatch.setattr(
        "utils.items_game_cache.ensure_future",
        lambda *a, **k: asyncio.get_event_loop().create_future(),
    )

    from utils import local_data as ld

    ld.TF2_SCHEMA = {"1": {"name": "A"}}
    ld.ITEMS_GAME_CLEANED = {"1": {"name": "B"}}
    monkeypatch.setenv("STEAM_API_KEY", "x")
    app = importlib.import_module("app")
    assert app.SCHEMA == mock_schema
