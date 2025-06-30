import json
import requests
import responses
import pytest

from utils import inventory_processor as ip
from utils import schema_cache as sc
from utils import schema_fetcher as sf
from utils import steam_api_client as sac
from utils import items_game_cache as ig


@pytest.fixture(autouse=True)
def no_items_game(monkeypatch):
    monkeypatch.setattr(ig, "ensure_items_game_cached", lambda: {})
    monkeypatch.setattr(ig, "ITEM_BY_DEFINDEX", {}, False)


@pytest.fixture(autouse=True)
def stub_schema(monkeypatch):
    mapping = {
        111: {
            "defindex": 111,
            "base_name": "Rocket Launcher",
            "image_url": "https://steamcommunity-a.akamaihd.net/economy/image/img/360fx360f",
        },
        222: {"defindex": 222, "base_name": "Team Captain", "image_url": "img"},
        1: {
            "defindex": 1,
            "base_name": "One",
            "image_url": "https://steamcommunity-a.akamaihd.net/economy/image/a/360fx360f",
        },
        2: {"defindex": 2, "base_name": "Two", "image_url": ""},
        5: {
            "defindex": 5,
            "base_name": "Abs",
            "image_url": "http://example.com/icon.png",
        },
    }

    monkeypatch.setattr(sc, "get_item", lambda idx: mapping[idx])
    monkeypatch.setattr(
        sc,
        "get_quality",
        lambda q: {
            11: ("Strange", "#CF6A32"),
            5: ("Unusual", "#B2B2B2"),
            6: ("Unique", "#B2B2B2"),
            0: ("Normal", "#B2B2B2"),
        }.get(q),
    )
    monkeypatch.setattr(sc, "get_origin", lambda o: None)
    monkeypatch.setattr(sc, "get_sheen", lambda sid: {701: "Team Shine"}.get(sid))
    monkeypatch.setattr(
        sc, "get_killstreaker", lambda kid: {2002: "Fire Horns"}.get(kid)
    )
    monkeypatch.setattr(
        sc,
        "get_effect",
        lambda eid: {13: "Burning Flames", 2003: "Cerebral Discharge"}.get(eid),
    )
    monkeypatch.setattr(
        sc, "get_strange_part", lambda aid: {380: "Buildings Destroyed"}.get(aid)
    )
    monkeypatch.setattr(
        sc,
        "get_spell",
        lambda bit: {1: "Exorcism", 4: "Footprints", 8: "Pumpkin Bombs"}.get(bit),
    )
    monkeypatch.setattr(
        sc, "_SPELLS", {1: "Exorcism", 4: "Footprints", 8: "Pumpkin Bombs"}, False
    )


def test_enrich_inventory():
    data = {"items": [{"defindex": 111, "quality": 11}]}
    sf.SCHEMA = {
        "111": {
            "defindex": 111,
            "item_name": "Rocket Launcher",
            "image_url": "https://steamcommunity-a.akamaihd.net/economy/image/img/360fx360f",
        }
    }
    sf.QUALITIES = {"11": "Strange"}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Strange Rocket Launcher"
    assert items[0]["quality"] == "Strange"
    assert items[0]["quality_color"] == "#CF6A32"
    assert items[0]["image_url"].startswith(
        "https://steamcommunity-a.akamaihd.net/economy/image/"
    )


def test_enrich_inventory_unusual_effect(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 222,
                "quality": 5,
                "descriptions": [{"value": "Unusual Effect: Burning Flames"}],
            }
        ]
    }
    sf.SCHEMA = {
        "222": {"defindex": 222, "item_name": "Team Captain", "image_url": "img"}
    }
    sf.QUALITIES = {"5": "Unusual"}
    monkeypatch.setattr(sc, "get_effect", lambda eid: {13: "Burning Flames"}.get(eid))
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Burning Flames Team Captain"
    assert items[0]["quality"] == "Unusual"


def test_process_inventory_handles_missing_icon():
    data = {"items": [{"defindex": 1}, {"defindex": 2}]}
    sf.SCHEMA = {
        "1": {
            "defindex": 1,
            "item_name": "One",
            "image_url": "https://steamcommunity-a.akamaihd.net/economy/image/a/360fx360f",
        },
        "2": {"defindex": 2, "item_name": "Two", "image_url": ""},
    }
    sf.QUALITIES = {}
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
    sf.SCHEMA = {"5": {"defindex": 5, "item_name": "Abs", "image_url": url}}
    sf.QUALITIES = {"0": "Normal"}
    items = ip.enrich_inventory(data)
    assert items[0]["image_url"] == url


def test_enrich_inventory_skips_unknown_defindex(monkeypatch):
    data = {"items": [{"defindex": 1}, {"defindex": 2}]}
    sf.SCHEMA = {"1": {"defindex": 1, "item_name": "One", "image_url": "a"}}
    sf.QUALITIES = {}
    monkeypatch.setattr(
        sc,
        "get_item",
        lambda idx: {1: {"defindex": 1, "base_name": "One", "image_url": "a"}}.get(idx)
        or (_ for _ in ()).throw(KeyError()),
    )
    items = ip.enrich_inventory(data)
    assert len(items) == 1
    assert items[0]["name"] == "One"


def test_enrich_inventory_killstreak_effect_from_attribute(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 111,
                "quality": 6,
                "attributes": [{"defindex": 2071, "float_value": 2003}],
            }
        ]
    }
    sf.SCHEMA = {"111": {"defindex": 111, "item_name": "Rocket", "image_url": "i"}}
    sf.QUALITIES = {"6": "Unique"}
    monkeypatch.setattr(
        sc, "get_killstreaker", lambda kid: {2003: "Cerebral Discharge"}.get(kid)
    )
    items = ip.enrich_inventory(data)
    assert items[0]["killstreaker"] == "Cerebral Discharge"


def test_enrich_inventory_spells_bitmask():
    data = {
        "items": [
            {
                "defindex": 111,
                "attributes": [{"defindex": 730, "float_value": 5}],
            }
        ]
    }
    sf.SCHEMA = {"111": {"defindex": 111, "item_name": "Rocket", "image_url": "i"}}
    sf.QUALITIES = {}
    items = ip.enrich_inventory(data)
    assert set(items[0]["spells"]) == {"Exorcism", "Footprints"}


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
    url = "https://api.steampowered.com/IEconItems_440/GetPlayerItems/v0001/?key=x&steamid=1"
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, url, **payload)
        status, data = sac.fetch_inventory("1")
    assert status == expected


@pytest.mark.parametrize("status", ["parsed", "incomplete", "private"])
def test_user_template_safe(monkeypatch, status):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr("utils.schema_fetcher.ensure_schema_cached", lambda: {})
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


def test_enrich_inventory_pro_item(monkeypatch):
    with open("tests/fixtures/pro_item.json") as f:
        asset = json.load(f)

    data = {"items": [asset]}
    sf.SCHEMA = {"222": {"defindex": 222, "item_name": "Rocket", "image_url": "i"}}
    sf.QUALITIES = {"6": "Unique"}
    monkeypatch.setattr(sc, "get_sheen", lambda sid: {701: "Team Shine"}.get(sid))
    monkeypatch.setattr(
        sc, "get_killstreaker", lambda kid: {2002: "Fire Horns"}.get(kid)
    )
    monkeypatch.setattr(
        sc, "get_strange_part", lambda aid: {380: "Buildings Destroyed"}.get(aid)
    )
    monkeypatch.setattr(
        sc, "get_spell", lambda bit: {4: "Footprints", 8: "Pumpkin Bombs"}.get(bit)
    )
    monkeypatch.setattr(sc, "get_effect", lambda eid: {13: "Burning Flames"}.get(eid))
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["spells"] == ["Footprints", "Pumpkin Bombs"]
    assert item["killstreak_tier"] == "Professional"
    assert item["sheen"] == "Team Shine"
    assert item["killstreaker"] == "Fire Horns"
    assert item["strange_parts"] == ["Buildings Destroyed"]
    assert item["is_festivized"] is True
    assert item["unusual_effect"] == "Burning Flames"
    icons = [b["icon"] for b in item.get("badges", [])]
    for ic in ["🎄", "🔥", "👣", "🎃", "⚔️", "💀", "✨", "📊"]:
        assert ic in icons
