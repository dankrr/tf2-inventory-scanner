import importlib
import json
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


def test_item_data_attribute_remains_single_quoted(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "Decorated Weapon Flamethrower",
                    "display_name": "Warhawk Flamethrower",
                    "quality_color": "#fff",
                    "grade_name": "Elite Grade",
                    "wear_name": "Factory New",
                }
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    assert "data-item='" in html


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
    assert "is-uncraftable" in classes


def test_uncraftable_data_item_flags_and_badge_rendered(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "Widget",
                    "image_url": "",
                    "quality_color": "#fff",
                    "craftable": False,
                    "is_craftable": False,
                    "uncraftable": True,
                    "is_uncraftable": True,
                    "craftability_source": "flag_cannot_craft",
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
    payload = json.loads(card["data-item"])
    assert payload["craftable"] is False
    assert payload["is_uncraftable"] is True
    badge = soup.find("span", class_="uncraftable-badge")
    assert badge is not None


def test_craftable_item_does_not_render_uncraftable_badge(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "Craftable Widget",
                    "image_url": "",
                    "quality_color": "#fff",
                    "craftable": True,
                    "is_craftable": True,
                    "uncraftable": False,
                    "is_uncraftable": False,
                }
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    soup = BeautifulSoup(html, "html.parser")
    assert soup.find("span", class_="uncraftable-badge") is None


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


def test_grade_badge_uses_short_label_and_card_keeps_quality_style(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "Decorated Test",
                    "display_name": "Decorated Test",
                    "quality_color": "#123456",
                    "border_color": "#123456",
                    "grade_name": "Commando Grade",
                    "grade_short_name": "Commando",
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
    assert "grade-commando-grade" not in card.get("class", [])
    assert "--quality-color: #123456" in card.get("style", "")
    grade_chip = soup.find("span", class_="grade-badge")
    assert grade_chip is not None
    assert grade_chip.text.strip() == "Commando"


def test_user_summary_counts_spelled_items(app):
    context = {
        "user": {
            "items": [
                {"name": "A", "image_url": "", "spells": ["Exorcism"]},
                {"name": "B", "image_url": "", "has_spells": True},
                {"name": "C", "image_url": "", "spell_names": ["Halloween Fire"]},
                {"name": "D", "image_url": ""},
            ]
        }
    }
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    assert "Spells:" in html
    assert "> 3<" in html or "Spells:</span> 3" in html
