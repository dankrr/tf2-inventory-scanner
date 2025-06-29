from utils import inventory_processor as ip
from utils import steam_api_client as sac
from utils import items_game_cache as ig
from utils import local_data as ld
import requests
import responses
import pytest


@pytest.fixture(autouse=True)
def no_items_game(monkeypatch):
    monkeypatch.setattr(ig, "ensure_items_game_cached", lambda: {})
    monkeypatch.setattr(ig, "ITEM_BY_DEFINDEX", {}, False)
    ld.TF2_SCHEMA = {}
    ld.ITEMS_GAME_CLEANED = {}


def test_enrich_inventory():
    data = {"items": [{"defindex": 111, "quality": 11}]}
    ld.TF2_SCHEMA = {
        "111": {
            "defindex": 111,
            "item_name": "Rocket Launcher",
            "image_url": "https://steamcommunity-a.akamaihd.net/economy/image/img/360fx360f",
        }
    }
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Strange Rocket Launcher"
    assert items[0]["quality"] == "Strange"
    assert items[0]["quality_color"] == "#CF6A32"
    assert items[0]["image_url"].startswith(
        "https://steamcommunity-a.akamaihd.net/economy/image/"
    )


def test_enrich_inventory_unusual_effect():
    data = {
        "items": [
            {
                "defindex": 222,
                "quality": 5,
                "descriptions": [{"value": "Unusual Effect: Burning Flames"}],
            }
        ]
    }
    ld.TF2_SCHEMA = {
        "222": {"defindex": 222, "item_name": "Team Captain", "image_url": "img"}
    }
    ld.EFFECT_NAMES = {"13": "Burning Flames"}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Burning Flames Team Captain"
    assert items[0]["quality"] == "Unusual"


def test_process_inventory_handles_missing_icon():
    data = {"items": [{"defindex": 1}, {"defindex": 2}]}
    ld.TF2_SCHEMA = {
        "1": {
            "defindex": 1,
            "item_name": "One",
            "image_url": "https://steamcommunity-a.akamaihd.net/economy/image/a/360fx360f",
        },
        "2": {"defindex": 2, "item_name": "Two", "image_url": ""},
    }
    items = ip.process_inventory(data)
    assert {i["name"] for i in items} == {"One", "Two"}
    for item in items:
        if item["name"] == "One":
            assert item["image_url"].startswith(
                "https://steamcommunity-a.akamaihd.net/economy/image/"
            )
        else:
            assert item["image_url"] == ""


def test_enrich_inventory_preserves_absolute_url():
    data = {"items": [{"defindex": 5, "quality": 0}]}
    url = "http://example.com/icon.png"
    ld.TF2_SCHEMA = {"5": {"defindex": 5, "item_name": "Abs", "image_url": url}}
    items = ip.enrich_inventory(data)
    assert items[0]["image_url"] == url


def test_enrich_inventory_skips_unknown_defindex():
    data = {"items": [{"defindex": 1}, {"defindex": 2}]}
    ld.TF2_SCHEMA = {"1": {"defindex": 1, "item_name": "One", "image_url": "a"}}
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
    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", lambda: {})
    monkeypatch.setattr(
        "utils.autobot_schema_cache.ensure_all_cached", lambda *a, **k: None
    )
    monkeypatch.setattr("utils.local_data.load_files", lambda: ({}, {}))
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
        items=[{"image_url": ""}] if status == "parsed" else [],
        status=status,
    )

    with app.app.app_context():
        app.render_template("_user.html", user=user)
