import importlib
import json

import pytest
from flask import render_template_string
from bs4 import BeautifulSoup

HTML = '{% include "_user.html" %}'


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr("utils.local_data.load_files", lambda: ({}, {}))
    mod = importlib.import_module("app")
    importlib.reload(mod)
    return mod.app


def test_item_badges_rendered(app):
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
    with app.app_context():
        app_module = importlib.import_module("app")
        user_ns = app_module.normalize_user_payload(user)
        html = render_template_string(HTML, user=user_ns)
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", class_="item-card")
    data = json.loads(card["data-item"])
    assert data["badges"] == item["badges"]
