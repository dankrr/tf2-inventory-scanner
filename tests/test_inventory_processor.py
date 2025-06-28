# ruff: noqa: E402
import os

os.environ.setdefault("BACKPACK_API_KEY", "x")

from utils import inventory_processor as ip
from utils import schema_fetcher as sf
from utils import steam_api_client as sac
import requests
import responses
import pytest


def test_enrich_inventory():
    data = {"items": [{"defindex": 111, "quality": 0}]}
    sf.SCHEMA = {
        "111;0;1": {
            "defindex": 111,
            "name": "Test Item",
            "image_url": "img",
            "quality": 0,
            "craftable": True,
        }
    }
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Test Item"
    assert items[0]["quality"] == "Normal"
    assert items[0]["quality_color"] == "#B2B2B2"
    assert items[0]["final_url"].startswith(
        "https://steamcommunity.cloudflare.steamstatic.com/economy/image/"
    )


def test_process_inventory_handles_missing_icon():
    data = {"items": [{"defindex": 1}, {"defindex": 2}]}
    sf.SCHEMA = {
        "1;0;1": {
            "defindex": 1,
            "name": "One",
            "image_url": "a",
            "quality": 0,
            "craftable": True,
        },
        "2;0;1": {
            "defindex": 2,
            "name": "Two",
            "image_url": "",
            "quality": 0,
            "craftable": True,
        },
    }
    items = ip.process_inventory(data)
    assert {i["name"] for i in items} == {"One", "Two"}
    for item in items:
        if item["name"] == "One":
            assert item["final_url"].startswith(
                "https://steamcommunity.cloudflare.steamstatic.com/economy/image/"
            )
        else:
            assert item["final_url"] == ""


def test_enrich_inventory_preserves_absolute_url():
    data = {"items": [{"defindex": 5, "quality": 0}]}
    url = "http://example.com/icon.png"
    sf.SCHEMA = {
        "5;0;1": {
            "defindex": 5,
            "name": "Abs",
            "image_url": url,
            "quality": 0,
            "craftable": True,
        }
    }
    items = ip.enrich_inventory(data)
    assert items[0]["final_url"] == url


def test_enrich_inventory_skips_unknown_defindex():
    data = {"items": [{"defindex": 1}, {"defindex": 2}]}
    sf.SCHEMA = {
        "1;0;1": {
            "defindex": 1,
            "name": "One",
            "image_url": "a",
            "quality": 0,
            "craftable": True,
        }
    }
    items = ip.enrich_inventory(data)
    assert len(items) == 1
    assert items[0]["name"] == "One"


def test_get_inventories_adds_user_agent(monkeypatch):
    captured = {}

    class DummyResp:
        def __init__(self, status=200):
            self.status_code = status

        def raise_for_status(self):
            if self.status_code != 200:
                raise requests.HTTPError(response=self)

        def json(self):
            return {"result": {"items": []}}

    def fake_get(url, headers=None, timeout=10):
        captured["ua"] = headers.get("User-Agent") if headers else None
        return DummyResp()

    monkeypatch.setattr(sac.requests, "get", fake_get)
    sac.get_inventories(["1"])
    assert captured["ua"] == "Mozilla/5.0"


def test_fetch_inventory_handles_http_error(monkeypatch):
    def fake_fetch(_id):
        return "failed", {}

    monkeypatch.setattr(sac, "fetch_inventory", fake_fetch)
    data, status = ip.fetch_inventory("1")
    assert data == {"items": []}
    assert status == "failed"


@pytest.mark.parametrize(
    "payload,expected",
    [
        (
            {"status": 200, "json": {"result": {"status": 1, "items": [{"id": 1}]}}},
            "parsed",
        ),
        ({"status": 200, "json": {"result": {"status": 1, "items": []}}}, "incomplete"),
        ({"status": 200, "json": {"result": {"status": 15}}}, "private"),
        ({"body": requests.ConnectionError()}, "failed"),
    ],
)
def test_fetch_inventory_statuses(monkeypatch, payload, expected):
    monkeypatch.setattr(sac, "STEAM_API_KEY", "x")
    url = (
        "https://api.steampowered.com/IEconItems_440/GetPlayerItems/v0001/"
        "?key=x&steamid=1"
    )
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, url, **payload)
        status, data = sac.fetch_inventory("1")
    assert status == expected


@pytest.mark.parametrize("status", ["parsed", "incomplete", "private"])
def test_user_template_safe(monkeypatch, status):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BACKPACK_API_KEY", "x")
    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", lambda: {})
    import importlib

    app = importlib.import_module("app")
    importlib.reload(app)

    from types import SimpleNamespace

    user = SimpleNamespace(
        steamid="1",
        username="User",
        avatar="",
        playtime=0.0,
        profile="#",
        items=[{"final_url": ""}] if status == "parsed" else [],
        status=status,
    )

    with app.app.app_context():
        app.render_template("_user.html", user=user)
