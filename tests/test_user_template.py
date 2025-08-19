import importlib
from pathlib import Path

import pytest
from flask import render_template_string
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


@pytest.mark.parametrize(
    "context",
    [
        {"user": {"items": [{"name": "Foo", "image_url": ""}]}},
        {
            "user": {
                "items": [
                    {
                        "name": "Foo",
                        "image_url": "",
                        "badges": [{"icon": "★", "title": "Star"}],
                    }
                ]
            }
        },
        {"user": {"items": []}},
        {"user": {}},
    ],
)
def test_user_template_does_not_error(app, context):
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context.get("user", {}))
        render_template_string(HTML, **context)


def test_user_template_renders_badge_icon(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "Bar",
                    "image_url": "",
                    "badges": [{"icon": "★", "title": "Star"}],
                }
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    assert "★" in html


def test_user_template_renders_paint_spell_badge(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "Painted Hat",
                    "image_url": "",
                    "badges": [{"icon": "🖌", "title": "Paint Spell"}],
                }
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    assert "🖌" in html


def test_user_template_filters_hidden_items(app):
    context = {
        "user": {
            "items": [
                {"name": "Vis", "image_url": ""},
                {"name": "Hidden", "image_url": "", "_hidden": True},
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    assert "Vis" in html
    assert "Hidden" not in html


def test_unusual_effect_rendered(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "Burning Flames Cap",
                    "original_name": "Unusual Cap",
                    "display_name": "Burning Flames Cap",
                    "base_name": "Cap",
                    "unusual_effect_name": "Burning Flames",
                    "unusual_effect_id": 123,
                    "quality": "Unusual",
                    "strange": True,
                    "image_url": "",
                    "quality_color": "#fff",
                }
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", class_="item-card")
    assert card is not None
    assert card.get("title") == "Burning Flames Cap"


def test_war_paint_tool_target_displayed(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "War Paint",
                    "display_name": "War Paint: Warhawk (Field-Tested)",
                    "image_url": "",
                    "badges": [],
                    "warpaint_name": "Warhawk",
                    "target_weapon_name": "Rocket Launcher",
                    "is_war_paint_tool": True,
                    "quality_color": "#fff",
                }
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    assert "Rocket Launcher" in html


def test_decorated_quality_not_shown(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "Decorated Weapon Flamethrower",
                    "composite_name": "Warhawk Flamethrower",
                    "display_name": "Warhawk Flamethrower",
                    "image_url": "",
                    "quality": "Decorated Weapon",
                    "quality_color": "#fff",
                }
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", class_="item-card")
    assert card is not None
    assert card.get("title") == "Warhawk Flamethrower"


def test_failed_user_has_retry_class(app):
    context = {"user": {"steamid": "123", "status": "failed", "items": []}}
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", {"data-steamid": "123"})
    assert card is not None
    classes = card.get("class", [])
    assert "retry-card" in classes


def test_trade_hold_class_rendered(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "Widget",
                    "image_url": "",
                    "quality_color": "#fff",
                    "untradable_hold": True,
                }
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", class_="item-card")
    assert card is not None
    classes = card.get("class", [])
    assert "trade-hold" in classes


def test_uncraftable_class_rendered(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "Gadget",
                    "image_url": "",
                    "quality_color": "#fff",
                    "uncraftable": True,
                }
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", class_="item-card")
    assert card is not None
    classes = card.get("class", [])
    assert "uncraftable" in classes


def test_elevated_strange_class_rendered(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "Gadget",
                    "image_url": "",
                    "quality_color": "#00ff00",
                    "border_color": "#CF6A32",
                    "has_strange_tracking": True,
                }
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", class_="item-card")
    assert card is not None
    classes = card.get("class", [])
    assert "elevated-strange" in classes
    assert card.get("title") == "Gadget"


def test_australium_name_omits_strange_prefix(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "Strange Australium Scattergun",
                    "display_name": "Australium Scattergun",
                    "base_name": "Scattergun",
                    "is_australium": True,
                    "quality": "Strange",
                    "image_url": "",
                    "quality_color": "#fff",
                }
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", class_="item-card")
    assert card is not None
    assert card.get("title") == "Australium Scattergun"


def test_professional_killstreak_australium_title(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "Professional Killstreak Australium Scattergun",
                    "display_name": "Australium Scattergun",
                    "base_name": "Scattergun",
                    "killstreak_name": "Professional",
                    "is_australium": True,
                    "quality": "Strange",
                    "image_url": "",
                    "quality_color": "#fff",
                }
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", class_="item-card")
    assert card is not None
    assert card.get("title") == "Professional Killstreak Australium Scattergun"
