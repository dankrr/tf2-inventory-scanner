import importlib


def test_app_uses_mock_schema(monkeypatch):
    mock_schema = {"5": {"defindex": 5, "name": "Five"}}

    def fake_ensure():
        return mock_schema

    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", fake_ensure)
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BACKPACK_API_KEY", "x")
    app = importlib.import_module("app")
    assert app.SCHEMA == mock_schema
