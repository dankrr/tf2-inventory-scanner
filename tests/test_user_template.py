import importlib

import pytest
from flask import render_template_string

HTML = '{% include "_user.html" %}'


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", lambda: {})
    mod = importlib.import_module("app")
    importlib.reload(mod)
    return mod.app


@pytest.mark.parametrize(
    "context",
    [
        {"user": {"items": [{"name": "Foo", "final_url": "", "image_url": ""}]}},
        {"user": {"items": []}},
        {"user": {}},
    ],
)
def test_user_template_does_not_error(app, context):
    with app.app_context():
        app_module = importlib.import_module("app")
        context["user"] = app_module.normalize_user_payload(context.get("user", {}))
        render_template_string(HTML, **context)


def test_item_card_has_valid_json(app):
    with app.app_context():
        app_module = importlib.import_module("app")
        user = {
            "items": [
                {
                    "name": "Foo",
                    "final_url": "",
                    "image_url": "",
                    "quality_color": "#fff",
                    "badges": [],
                }
            ]
        }
        user_ns = app_module.normalize_user_payload(user)
        html = render_template_string(HTML, user=user_ns)

        from html.parser import HTMLParser

        class Parser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.data = None

            def handle_starttag(self, tag, attrs):
                if tag == "div":
                    attr = dict(attrs)
                    cls = attr.get("class", "")
                    if "item-card" in cls.split():
                        self.data = attr.get("data-item")

        parser = Parser()
        parser.feed(html)
        import json

        json.loads(parser.data)
