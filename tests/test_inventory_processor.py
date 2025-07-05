from utils import inventory_processor as ip
from utils import steam_api_client as sac
from utils import local_data as ld
import requests
import responses
import pytest


@pytest.fixture(autouse=True)
def reset_data(monkeypatch):
    ld.ITEMS_BY_DEFINDEX = {}
    ld.SCHEMA_ATTRIBUTES = {}


def test_enrich_inventory():
    data = {"items": [{"defindex": 111, "quality": 11}]}
    ld.ITEMS_BY_DEFINDEX = {
        111: {
            "item_name": "Rocket Launcher",
            "image_url": "https://steamcommunity-a.akamaihd.net/economy/image/img/360fx360f",
        }
    }
    ld.QUALITIES_BY_INDEX = {11: "Strange"}
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
                "attributes": [{"defindex": 134, "float_value": 13}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {222: {"item_name": "Team Captain", "image_url": "img"}}
    ld.QUALITIES_BY_INDEX = {5: "Unusual"}
    ld.EFFECT_NAMES = {"13": "Burning Flames"}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Unusual Team Captain"
    assert items[0]["display_name"] == "Burning Flames Team Captain"
    assert items[0]["unusual_effect"] == "Burning Flames"
    assert items[0]["quality"] == "Unusual"


@pytest.mark.parametrize(
    "quality,expected",
    [
        (5, True),
        (11, False),
        (6, False),
    ],
)
def test_unusual_effect_only_for_allowed_qualities(quality, expected):
    data = {
        "items": [
            {
                "defindex": 333,
                "quality": quality,
                "attributes": [{"defindex": 134, "float_value": 13}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {333: {"item_name": "Cap", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {5: "Unusual", 11: "Haunted", 6: "Unique"}
    ld.EFFECT_NAMES = {"13": "Burning Flames"}
    items = ip.enrich_inventory(data)
    effect = items[0]["unusual_effect"]
    if expected:
        assert effect == "Burning Flames"
    else:
        assert effect is None


def test_process_inventory_handles_missing_icon():
    data = {"items": [{"defindex": 1}, {"defindex": 2}]}
    ld.ITEMS_BY_DEFINDEX = {
        1: {
            "item_name": "One",
            "image_url": "https://steamcommunity-a.akamaihd.net/economy/image/a/360fx360f",
        },
        2: {"item_name": "Two", "image_url": ""},
    }
    ld.QUALITIES_BY_INDEX = {}
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
    ld.ITEMS_BY_DEFINDEX = {5: {"item_name": "Abs", "image_url": url}}
    ld.QUALITIES_BY_INDEX = {0: "Normal"}
    items = ip.enrich_inventory(data)
    assert items[0]["image_url"] == url


def test_enrich_inventory_skips_unknown_defindex():
    data = {"items": [{"defindex": 1}, {"defindex": 2}]}
    ld.ITEMS_BY_DEFINDEX = {1: {"item_name": "One", "image_url": "a"}}
    ld.QUALITIES_BY_INDEX = {}
    items = ip.enrich_inventory(data)
    assert len(items) == 1
    assert items[0]["name"] == "One"


def test_custom_name_stored_separately(monkeypatch):
    data = {"items": [{"defindex": 444, "quality": 6, "custom_name": "Named"}]}
    ld.ITEMS_BY_DEFINDEX = {444: {"item_name": "Thing", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Thing"
    assert items[0]["custom_name"] == "Named"


def test_unusual_effect_quality_filter(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 500,
                "quality": 5,
                "attributes": [{"defindex": 134, "float_value": 15}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {500: {"item_name": "Hat", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {5: "Unusual"}
    ld.EFFECT_NAMES = {"15": "Burning Flames"}
    items = ip.enrich_inventory(data)
    assert items[0]["unusual_effect"] == "Burning Flames"

    # quality not allowed
    data = {
        "items": [
            {
                "defindex": 501,
                "quality": 6,
                "attributes": [{"defindex": 134, "float_value": 15}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {501: {"item_name": "Thing", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    items = ip.enrich_inventory(data)
    assert items[0]["unusual_effect"] is None


def test_unusual_effect_attribute_object():
    data = {
        "items": [
            {
                "defindex": 700,
                "quality": 5,
                "attributes": [{"defindex": 134, "float_value": 13}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {700: {"item_name": "Hat", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {5: "Unusual"}
    ld.EFFECT_NAMES = {"13": "Burning Flames"}
    items = ip.enrich_inventory(data)
    assert items[0]["unusual_effect"] == "Burning Flames"


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
    monkeypatch.setattr("utils.local_data.load_files", lambda *a, **k: ({}, {}))
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


def test_paint_and_paintkit_badges(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 9000,
                "quality": 6,
                "attributes": [
                    {"defindex": 142, "float_value": 3100495},
                    {"defindex": 834, "float_value": 350},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {9000: {"item_name": "Painted", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    monkeypatch.setattr(ld, "PAINT_NAMES", {"3100495": "Test Paint"}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"350": "Test Kit"}, False)

    items = ip.enrich_inventory(data)
    badges = items[0]["badges"]

    assert {
        "icon": "\U0001f3a8",
        "title": "Paint: Test Paint",
        "label": "Test Paint",
        "type": "paint",
    } in badges
    assert {
        "icon": "\U0001f58c",
        "title": "Warpaint: Test Kit",
        "label": "Test Kit",
        "type": "warpaint",
    } in badges


def test_schema_name_used_for_key():
    data = {"items": [{"defindex": 5021, "quality": 6}]}
    ld.ITEMS_BY_DEFINDEX = {5021: {"item_name": "Mann Co. Supply Crate Key"}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Mann Co. Supply Crate Key"


def test_placeholder_name_falls_back_to_schema():
    data = {"items": [{"defindex": 1001, "quality": 6}]}
    ld.ITEMS_BY_DEFINDEX = {1001: {"item_name": "Sniper Rifle"}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Sniper Rifle"


def test_paintkit_appended_to_name(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15141,
                "quality": 15,
                "attributes": [{"defindex": 834, "float_value": 350}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {15141: {"item_name": "Flamethrower"}}
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Decorated Weapon Flamethrower (Warhawk)"


def test_kill_eater_fields(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 111,
                "quality": 11,
                "attributes": [
                    {"defindex": 214, "value": 10},
                    {"defindex": 292, "float_value": 64},
                    {"defindex": 379, "value": 5},
                    {"defindex": 380, "float_value": 70},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {111: {"item_name": "Thing", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {11: "Strange"}
    monkeypatch.setattr(
        ld, "STRANGE_PART_NAMES", {"64": "Kills", "70": "Robots"}, False
    )
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["strange_count"] == 10
    assert item["score_type"] == "Kills"


def test_plain_craft_weapon_filtered():
    data = {"items": [{"defindex": 10, "quality": 6}]}
    ld.ITEMS_BY_DEFINDEX = {10: {"item_name": "A", "craft_class": "weapon"}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    items = ip.enrich_inventory(data)
    assert items == []


def test_special_craft_weapon_kept():
    data = {
        "items": [
            {
                "defindex": 11,
                "quality": 6,
                "attributes": [{"defindex": 2025, "value": 1}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {11: {"item_name": "B", "craft_class": "weapon"}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    items = ip.enrich_inventory(data)
    assert len(items) == 1
