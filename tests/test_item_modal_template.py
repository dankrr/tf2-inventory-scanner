import importlib
from pathlib import Path

import pytest
from flask import render_template
from bs4 import BeautifulSoup


@pytest.fixture
def app(monkeypatch):
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
    monkeypatch.setattr("utils.price_loader.build_price_map", lambda path: {})
    monkeypatch.setattr("utils.price_loader.PRICE_MAP_FILE", Path("price_map.json"))
    monkeypatch.setattr(
        "utils.price_loader.dump_price_map",
        lambda mapping, path=Path("price_map.json"): path,
    )
    mod = importlib.import_module("app")
    importlib.reload(mod)
    return mod.app


def test_killstreak_info_block(app):
    item = {
        "killstreak_name": "Professional Killstreak",
        "sheen_name": "Hot Rod",
        "sheen_color": "#8847ff",
        "killstreak_effect": "Fire Horns",
    }
    with app.app_context():
        html = render_template("_modal.html", item=item)
    soup = BeautifulSoup(html, "html.parser")
    info = soup.find("div", class_="killstreak-info")
    assert info is not None
    assert "Professional Killstreak" in info.text
    assert "Hot Rod" in info.text
    assert "Fire Horns" in info.text
    dot = info.find("span", class_="sheen-dot")
    assert dot is not None
    assert "#8847ff" in dot.get("style", "")


def test_craftable_text_shown(app):
    item = {"craftable": True}
    with app.app_context():
        html = render_template("_modal.html", item=item)
    soup = BeautifulSoup(html, "html.parser")
    assert "Craftable" in soup.text


def test_uncraftable_text_shown(app):
    item = {"craftable": False}
    with app.app_context():
        html = render_template("_modal.html", item=item)
    soup = BeautifulSoup(html, "html.parser")
    assert "Uncraftable" in soup.text
