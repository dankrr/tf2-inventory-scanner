import importlib
from pathlib import Path


def test_app_uses_mock_schema(monkeypatch):
    monkeypatch.setattr(
        "utils.schema_provider.SchemaProvider.refresh_all", lambda self: None
    )

    def fake_load(*args, **kwargs):
        from utils import local_data as ld

        ld.SCHEMA_ATTRIBUTES = {1: {"name": "Attr"}}
        ld.ITEMS_BY_DEFINDEX = {1: {"name": "B"}}
        return ld.SCHEMA_ATTRIBUTES, ld.ITEMS_BY_DEFINDEX

    monkeypatch.setattr("utils.local_data.load_files", fake_load)
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
    monkeypatch.setattr(
        "utils.price_loader.build_price_map",
        lambda path: {},
    )
    monkeypatch.setattr(
        "utils.price_loader.PRICE_MAP_FILE",
        Path("price_map.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.dump_price_map",
        lambda mapping, path=Path("price_map.json"): path,
    )
    app = importlib.import_module("app")
    assert hasattr(app, "app")
