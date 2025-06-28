import importlib


def test_app_uses_mock_schema(monkeypatch):
    mock_schema = {
        "5;0;1": {"defindex": 5, "name": "Five", "quality": 0, "craftable": True}
    }

    def fake_ensure():
        return mock_schema

    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", fake_ensure)
    monkeypatch.setattr(
        "utils.price_fetcher.ensure_prices_cached",
        lambda: {"5;0": {"value": 100, "currency": "metal", "last_update": 1}},
    )
    monkeypatch.setattr(
        "utils.price_fetcher.ensure_currencies_cached",
        lambda: {"metal": {"value": 1}, "keys": {"value": 1}},
    )
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BACKPACK_API_KEY", "x")
    app = importlib.import_module("app")
    assert app.SCHEMA == mock_schema
