import importlib
from pathlib import Path

from utils import inventory_processor as ip
from utils import local_data as ld

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
    title = soup.find("h2", class_="item-title")
    assert title is not None
    text = title.text.strip()
    assert text.startswith("Strange Cap")
    assert "Unusual" not in text


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
                    "composite_name": "Warhawk Flamethrower (Factory New)",
                    "display_name": "Warhawk Flamethrower (Factory New)",
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
    title = soup.find("h2", class_="item-title")
    assert title is not None
    assert title.text.strip() == "Warhawk Flamethrower (Factory New)"


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
    title = soup.find("h2", class_="item-title")
    assert title is not None
    assert title.text.strip() == "Australium Scattergun"


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
    title = soup.find("h2", class_="item-title")
    assert title is not None
    assert title.text.strip() == "Professional Killstreak Australium Scattergun"


def test_war_paint_tool_composite_name_title(app):
    context = {
        "user": {
            "items": [
                {
                    "name": "War Paint",
                    "composite_name": "Warhawk Rocket Launcher",
                    "image_url": "",
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
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h2", class_="item-title")
    assert title is not None
    assert title.text.strip() == "Warhawk Rocket Launcher"


def test_paintkitweapon_title_cleaned(app, monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15141,
                "quality": 15,
                "attributes": [
                    {"defindex": 834, "value": 350},
                    {"defindex": 749, "float_value": 0.0},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15141: {
            "item_name": "Paintkitweapon 1",
            "name": "Paintkitweapon 1",
            "craft_class": "weapon",
        }
    }
    ld.SCHEMA_ATTRIBUTES = {749: {"attribute_class": "texture_wear_default"}}
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"Warhawk": 350}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    item = ip.enrich_inventory(data)[0]
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context = {"user": {"items": [item]}}
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h2", class_="item-title")
    assert title is not None
    assert not title.text.strip().startswith("Paintkitweapon")


def test_paintkittool_title_cleaned(app, monkeypatch):
    data = {
        "items": [
            {
                "defindex": 5681,
                "quality": 6,
                "attributes": [
                    {"defindex": 134, "value": 350},
                    {"defindex": 725, "float_value": 0.2},
                    {"defindex": 2014, "value": 222},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        5681: {
            "item_name": "Paintkittool 5",
            "name": "Paintkittool 5",
            "item_class": "tool",
        },
        222: {"item_name": "Rocket Launcher"},
    }
    ld.SCHEMA_ATTRIBUTES = {725: {"attribute_class": "texture_wear_default"}}
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    item = ip.enrich_inventory(data)[0]
    with app.test_request_context():
        app_module = importlib.import_module("app")
        context = {"user": {"items": [item]}}
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h2", class_="item-title")
    assert title is not None
    assert not title.text.strip().startswith("Paintkittool")
