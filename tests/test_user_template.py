import importlib

import pytest
from flask import render_template_string

HTML = '{% include "_user.html" %}'


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BACKPACK_API_KEY", "x")
    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", lambda: {})
    mod = importlib.import_module("app")
    importlib.reload(mod)
    return mod.app


@pytest.mark.parametrize(
    "context",
    [
        {"user": {"items": [{"name": "Foo", "final_url": ""}]}},
        {"user": {"items": []}},
        {"user": {}},
    ],
)
def test_user_template_does_not_error(app, context):
    with app.app_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context.get("user", {}))
        render_template_string(HTML, **context)
