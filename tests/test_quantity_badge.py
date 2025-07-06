import importlib
from pathlib import Path
from flask import render_template_string
from bs4 import BeautifulSoup

HTML = '{% include "_user.html" %}'


def test_stack_items_collapses_duplicates():
    mod = importlib.import_module("app")
    items = [
        {"name": "Key", "image_url": "", "quality_color": "#fff"},
        {"name": "Key", "image_url": "", "quality_color": "#fff", "level": 10},
    ]
    result = mod.stack_items(items)
    assert len(result) == 1
    assert result[0]["quantity"] == 2


def test_quantity_badge_rendered(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BPTF_API_KEY", "x")
    monkeypatch.setattr(
        "utils.price_loader.ensure_prices_cached",
        lambda refresh=False: Path("prices.json"),
    )
    monkeypatch.setattr("utils.price_loader.build_price_map", lambda path: {})
    monkeypatch.setattr("utils.local_data.load_files", lambda *a, **k: ({}, {}))
    mod = importlib.import_module("app")
    importlib.reload(mod)
    item = {"name": "Key", "image_url": "", "quality_color": "#fff", "quantity": 3}
    user = {
        "steamid": "1",
        "profile": "",
        "avatar": "",
        "username": "Test",
        "playtime": 0,
        "status": "parsed",
        "items": [item],
    }
    with mod.app.app_context():
        user_ns = mod.normalize_user_payload(user)
        html = render_template_string(HTML, user=user_ns)
    soup = BeautifulSoup(html, "html.parser")
    badge = soup.find("span", class_="item-qty")
    assert badge.text.strip() == "x3"
