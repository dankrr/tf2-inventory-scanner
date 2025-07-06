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
    with app.app_context():
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
    with app.app_context():
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
    with app.app_context():
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
    with app.app_context():
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
                    "unusual_effect_name": "Burning Flames",
                    "image_url": "",
                    "quality_color": "#fff",
                }
            ]
        }
    }
    with app.app_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context["user"])
        html = render_template_string(HTML, **context)
    soup = BeautifulSoup(html, "html.parser")
    span = soup.find("span", class_="unusual-effect")
    assert span is None
    title = soup.find("h2", class_="item-title")
    assert title is not None
    assert title.text.strip().startswith("Burning Flames")
