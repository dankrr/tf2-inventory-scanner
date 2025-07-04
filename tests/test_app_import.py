import importlib


def test_app_uses_mock_schema(monkeypatch):
    monkeypatch.setattr(
        "utils.schema_provider.SchemaProvider.refresh_all", lambda self: None
    )

    def fake_load():
        from utils import local_data as ld

        ld.SCHEMA_ATTRIBUTES = {1: {"name": "Attr"}}
        ld.ITEMS_BY_DEFINDEX = {1: {"name": "B"}}
        return ld.SCHEMA_ATTRIBUTES, ld.ITEMS_BY_DEFINDEX

    monkeypatch.setattr("utils.local_data.load_files", fake_load)
    monkeypatch.setenv("STEAM_API_KEY", "x")
    app = importlib.import_module("app")
    assert hasattr(app, "app")
