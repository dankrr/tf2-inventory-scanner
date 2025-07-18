import importlib
import json
from pathlib import Path

import pytest
from quart import render_template_string
from bs4 import BeautifulSoup

HTML = '{% include "_user.html" %}'


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
    monkeypatch.setattr(
        "utils.price_loader.build_price_map",
        lambda path: {},
    )
    mod = importlib.import_module("app")
    importlib.reload(mod)
    return mod.app


@pytest.mark.asyncio
async def test_item_badges_rendered(app):
    item = {
        "name": "Rocket Launcher",
        "image_url": "http://example.com/rl.png",
        "quality_color": "#fff",
        "badges": [
            {"icon": "★", "title": "Unusual", "color": "#b00"},
            {"icon": "🎩", "title": "Vintage"},
            {"icon": "😎", "title": "Cool"},
        ],
    }
    user = {
        "steamid": "1",
        "profile": "",
        "avatar": "",
        "username": "Test",
        "playtime": 0,
        "status": "parsed",
        "items": [item],
    }
    async with app.app_context():
        app_module = importlib.import_module("app")
        user_ns = app_module.normalize_user_payload(user)
        html = await render_template_string(HTML, user=user_ns)
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", class_="item-card")
    data = json.loads(card["data-item"])
    assert data["badges"] == item["badges"]
