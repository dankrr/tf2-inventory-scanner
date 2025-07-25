import importlib
from pathlib import Path

import pytest
from quart import render_template
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


@pytest.mark.asyncio
async def test_killstreak_info_block(app):
    item = {
        "killstreak_name": "Professional Killstreak",
        "sheen_name": "Hot Rod",
        "sheen_color": "#8847ff",
        "sheen_colors": ["#8847ff"],
        "sheen_gradient_css": None,
        "killstreak_effect": "Fire Horns",
    }
    async with app.app_context():
        html = await render_template("_modal.html", item=item)
    soup = BeautifulSoup(html, "html.parser")
    info = soup.find("div", class_="killstreak-info")
    assert info is not None
    assert "Professional Killstreak" in info.text
    assert "Hot Rod" in info.text
    assert "Fire Horns" in info.text
    dot = info.find("span", class_="sheen-dot")
    assert dot is not None
    style = dot.get("style", "")
    assert "#8847ff" in style and "linear-gradient" not in style


@pytest.mark.asyncio
async def test_craftable_text_shown(app):
    item = {"craftable": True}
    async with app.app_context():
        html = await render_template("_modal.html", item=item)
    soup = BeautifulSoup(html, "html.parser")
    assert "Craftable" in soup.text


@pytest.mark.asyncio
async def test_uncraftable_text_shown(app):
    item = {"craftable": False}
    async with app.app_context():
        html = await render_template("_modal.html", item=item)
    soup = BeautifulSoup(html, "html.parser")
    assert "Uncraftable" in soup.text


@pytest.mark.asyncio
async def test_team_shine_gradient(app):
    item = {
        "killstreak_name": "Professional Killstreak",
        "sheen_name": "Team Shine",
        "sheen_color": "#cc3434",
        "sheen_colors": ["#cc3434", "#5885a2"],
        "sheen_gradient_css": "background: linear-gradient(90deg, #cc3434 50%, #5885a2 50%)",
    }
    async with app.app_context():
        html = await render_template("_modal.html", item=item)
    soup = BeautifulSoup(html, "html.parser")
    dot = soup.find("span", class_="sheen-dot")
    assert dot is not None
    style = dot.get("style", "")
    assert "linear-gradient" in style
    assert "#cc3434" in style and "#5885a2" in style
