from utils import inventory_processor as ip
from utils import schema_fetcher as sf
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
    sf.SCHEMA = {
        "222": {"defindex": 222, "item_name": "Team Captain", "image_url": "img"}
    }
    sf.QUALITIES = {"5": "Unusual"}
    ld.EFFECT_NAMES = {"13": "Burning Flames"}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Unusual Team Captain"
    assert items[0]["unusual_effect"] == "Burning Flames"
    assert items[0]["quality"] == "Unusual"


@pytest.mark.parametrize(
    "quality,expected",
    [
        (5, True),
        (11, True),
        (6, False),
    ],
)
def test_unusual_effect_only_for_allowed_qualities(quality, expected):
    data = {
        "items": [
            {
                "defindex": 333,
                "quality": quality,
                "descriptions": [{"value": "Unusual Effect: Burning Flames"}],
            }
        ]
    }
    sf.SCHEMA = {"333": {"defindex": 333, "item_name": "Cap", "image_url": ""}}
    sf.QUALITIES = {"5": "Unusual", "11": "Haunted", "6": "Unique"}
    ld.EFFECT_NAMES = {"13": "Burning Flames"}
    items = ip.enrich_inventory(data)
    effect = items[0]["unusual_effect"]
    if expected:
        assert effect == "Burning Flames"
    else:
        assert effect is None


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


def test_enrich_inventory_skips_unknown_defindex():
    data = {"items": [{"defindex": 1}, {"defindex": 2}]}
    sf.SCHEMA = {"1": {"defindex": 1, "item_name": "One", "image_url": "a"}}
    sf.QUALITIES = {}
    items = ip.enrich_inventory(data)
    assert len(items) == 1
    assert items[0]["name"] == "One"


def test_custom_name_stored_separately(monkeypatch):
    data = {"items": [{"defindex": 444, "quality": 6, "custom_name": "Named"}]}
    sf.SCHEMA = {"444": {"defindex": 444, "item_name": "Thing", "image_url": ""}}
    sf.QUALITIES = {"6": "Unique"}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Thing"
    assert items[0]["custom_name"] == "Named"


def test_unusual_effect_quality_filter(monkeypatch):
    data = {"items": [{"defindex": 500, "quality": 5, "effect": 15}]}
    sf.SCHEMA = {"500": {"defindex": 500, "item_name": "Hat", "image_url": ""}}
    sf.QUALITIES = {"5": "Unusual"}
    ld.EFFECT_NAMES = {"15": "Burning Flames"}
    items = ip.enrich_inventory(data)
    assert items[0]["unusual_effect"] == "Burning Flames"

    # quality not allowed
    data = {"items": [{"defindex": 501, "quality": 6, "effect": 15}]}
    sf.SCHEMA = {"501": {"defindex": 501, "item_name": "Thing", "image_url": ""}}
    sf.QUALITIES = {"6": "Unique"}
    items = ip.enrich_inventory(data)
    assert items[0]["unusual_effect"] is None


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


def test_paint_and_paintkit_badges(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 9000,
                "quality": 6,
                "attributes": [
                    {"defindex": 1257930978, "value": 3100495},
                    {"defindex": 834, "float_value": 350},
                ],
            }
        ]
    }
    sf.SCHEMA = {"9000": {"defindex": 9000, "item_name": "Painted", "image_url": ""}}
    sf.QUALITIES = {"6": "Unique"}
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"350": "Test Kit"}, False)

    items = ip.enrich_inventory(data)
    badges = items[0]["badges"]

    assert {
        "icon": "\U0001f3a8",
        "title": "Paint: A Color Similar to Slate",
        "color": "#2F4F4F",
        "type": "paint",
    } in badges
    assert {
        "icon": "\U0001f58c",
        "title": "Warpaint: Test Kit",
        "type": "warpaint",
    } in badges


def test_paint_extracted_from_value(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 9000,
                "quality": 6,
                "attributes": [
                    {"defindex": 1234, "float_value": 1065353216},
                    {"defindex": 1256537220, "value": 15158332},
                ],
            }
        ]
    }
    sf.SCHEMA = {"9000": {"defindex": 9000, "item_name": "Painted", "image_url": ""}}
    sf.QUALITIES = {"6": "Unique"}
    monkeypatch.setattr(ld, "PAINT_NAMES", {}, False)

    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["paint_name"] == "Australium Gold"
    assert item["paint_hex"] == "#E7B53B"


def test_schema_name_used_for_key():
    data = {"items": [{"defindex": 5021, "quality": 6}]}
    sf.SCHEMA = {"5021": {"defindex": 5021, "item_name": "Mann Co. Supply Crate Key"}}
    ld.ITEMS_GAME_CLEANED = {"5021": {"name": "Decoder Ring"}}
    sf.QUALITIES = {"6": "Unique"}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Mann Co. Supply Crate Key"


def test_placeholder_name_falls_back_to_schema():
    data = {"items": [{"defindex": 1001, "quality": 6}]}
    sf.SCHEMA = {"1001": {"defindex": 1001, "item_name": "Sniper Rifle"}}
    ld.ITEMS_GAME_CLEANED = {"1001": {"name": "rifle"}}
    sf.QUALITIES = {"6": "Unique"}
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
    sf.SCHEMA = {"15141": {"defindex": 15141, "item_name": "Flamethrower"}}
    ld.ITEMS_GAME_CLEANED = {"15141": {"name": "tf_weapon_flamethrower"}}
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"350": "Warhawk"}, False)
    sf.QUALITIES = {"15": "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Decorated Weapon Flamethrower (Warhawk)"
