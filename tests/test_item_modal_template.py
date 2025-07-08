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
    mod = importlib.import_module("app")
    importlib.reload(mod)
    return mod.app


def test_killstreak_badge_color(app):
    item = {"killstreak_name": "Professional Killstreak", "sheen_color": "#8847ff"}
    with app.app_context():
        html = render_template("_modal.html", item=item)
    soup = BeautifulSoup(html, "html.parser")
    badge = soup.find("span", class_="killstreak-badge")
    assert badge is not None
    assert badge.text.strip() == "Professional Killstreak"
    assert "#8847ff" in badge.get("style", "")
