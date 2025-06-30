import importlib

import pytest
from flask import render_template_string

HTML = '{% include "_user.html" %}'


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", lambda: {})
    monkeypatch.setattr("utils.local_data.load_files", lambda: ({}, {}))
    mod = importlib.import_module("app")
    importlib.reload(mod)
    return mod.app


@pytest.mark.parametrize(
    "context",
    [
        {"user": {"items": [{"name": "Foo", "image_url": ""}]}},
        {"user": {"items": []}},
        {"user": {}},
    ],
)
def test_user_template_does_not_error(app, context):
    with app.app_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context.get("user", {}))
        render_template_string(HTML, **context)


def test_user_card_uses_base_name(app):
    from types import SimpleNamespace

    user = SimpleNamespace(
        steamid="1",
        username="User",
        avatar="",
        playtime=0.0,
        profile="#",
        status="parsed",
        items=[
            {
                "name": "Strange Rocket Launcher",
                "base_name": "Rocket Launcher",
                "image_url": "",
                "custom_name": "My RL",
                "custom_desc": "Desc",
            }
        ],
    )
    with app.app_context():
        html = render_template_string(HTML, user=user)
        import re

        m = re.search(r'<div class="item-title">([^<]+)</div>', html)
        assert m and m.group(1) == "Rocket Launcher"
