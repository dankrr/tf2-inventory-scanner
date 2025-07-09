import asyncio
from pathlib import Path
import aiohttp
import pytest
from utils import inventory_processor as ip
from utils import steam_api_client as sac
from utils import local_data as ld
from utils.valuation_service import ValuationService


@pytest.fixture(autouse=True)
def reset_data(monkeypatch):
    ld.ITEMS_BY_DEFINDEX = {}
    ld.SCHEMA_ATTRIBUTES = {}


@pytest.fixture
def patch_valuation(monkeypatch):
    def _apply(price_map):
        service = ValuationService(price_map=price_map)
        monkeypatch.setattr(ip, "get_valuation_service", lambda: service)
        return service

    return _apply


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
    item = items[0]
    assert item["name"] == "Burning Flames Team Captain"
    assert item["original_name"] == "Unusual Team Captain"
    assert item["display_name"] == "Burning Flames Team Captain"
    assert item["unusual_effect"] == {"id": 13, "name": "Burning Flames"}
    assert item["quality"] == "Unusual"


def test_unusual_effect_badge_included():
    data = {
        "items": [
            {
                "defindex": 7000,
                "quality": 5,
                "attributes": [{"defindex": 134, "float_value": 13}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {7000: {"item_name": "Hat", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {5: "Unusual"}
    ld.EFFECT_NAMES = {"13": "Burning Flames"}

    items = ip.enrich_inventory(data)
    badges = items[0]["badges"]
    assert {
        "icon": "★",
        "title": "Unusual Effect: Burning Flames",
        "color": "#8650AC",
        "label": "Burning Flames",
        "type": "effect",
    } in badges


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
        assert effect == {"id": 13, "name": "Burning Flames"}
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


def test_enrich_inventory_unknown_defindex_kept():
    data = {"items": [{"defindex": 1}, {"defindex": 2}]}
    ld.ITEMS_BY_DEFINDEX = {1: {"item_name": "One", "image_url": "a"}}
    ld.QUALITIES_BY_INDEX = {}
    items = ip.enrich_inventory(data)
    assert len(items) == 2
    assert items[0]["name"] == "One"
    assert items[1]["base_name"] == "Unknown Weapon"


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
    assert items[0]["unusual_effect"] == {"id": 15, "name": "Burning Flames"}

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
    assert items[0]["unusual_effect"] == {"id": 13, "name": "Burning Flames"}


def test_unusual_effect_attribute_object_2041():
    data = {
        "items": [
            {
                "defindex": 701,
                "quality": 5,
                "attributes": [{"defindex": 2041, "value": 13}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {701: {"item_name": "Hat", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {5: "Unusual"}
    ld.EFFECT_NAMES = {"13": "Burning Flames"}
    items = ip.enrich_inventory(data)
    assert items[0]["unusual_effect"] == {"id": 13, "name": "Burning Flames"}


def test_unusual_taunt_effect_badge():
    data = {
        "items": [
            {
                "defindex": 6001,
                "quality": 5,
                "attributes": [{"defindex": 134, "float_value": 3009}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {6001: {"item_name": "Taunt: Conga", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {5: "Unusual"}
    ld.EFFECT_NAMES = {"3009": "Silver Cyclone"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["badges"][0]["icon"] == "★"
    assert item["unusual_effect_name"] == "Silver Cyclone"
    assert "Silver Cyclone" in item["name"]


def test_get_inventories_adds_user_agent(monkeypatch):
    captured = {}

    class DummyResp:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def raise_for_status(self):
            pass

        async def json(self):
            return {"result": {"items": []}}

    class DummyRequestCtx:
        def __init__(self, resp):
            self.resp = resp

        def __await__(self):
            async def _coro():
                return self.resp

            return _coro().__await__()

        async def __aenter__(self):
            return self.resp

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def get(self, url, headers=None, timeout=None):
            captured["ua"] = headers.get("User-Agent") if headers else None
            return DummyRequestCtx(DummyResp())

    monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **k: DummySession())
    asyncio.run(sac.get_inventories(["1"]))
    assert captured["ua"] == "Mozilla/5.0"


def test_fetch_inventory_handles_http_error(monkeypatch):
    async def fake_fetch(_id):
        return "failed", {}

    monkeypatch.setattr(sac, "fetch_inventory", fake_fetch)
    data, status = asyncio.run(ip.fetch_inventory("1"))
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
        ({"body": aiohttp.ClientError()}, "failed"),
    ],
)
def test_fetch_inventory_statuses(monkeypatch, payload, expected):
    monkeypatch.setattr(sac, "STEAM_API_KEY", "x")
    url = (
        "https://api.steampowered.com/IEconItems_440/GetPlayerItems/v0001/"
        "?key=x&steamid=1"
    )

    class DummyResp:
        status = payload.get("status", 200)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def raise_for_status(self):
            if self.status >= 400:
                raise aiohttp.ClientResponseError(None, None, status=self.status)

        async def json(self):
            return payload.get("json", {})

    class DummyRequestCtx:
        def __init__(self, resp):
            self.resp = resp

        def __await__(self):
            async def _coro():
                return self.resp

            return _coro().__await__()

        async def __aenter__(self):
            return self.resp

        async def __aexit__(self, exc_type, exc, tb):
            pass

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def get(self, url_arg, **kwargs):
            assert url_arg == url
            if "body" in payload:
                raise aiohttp.ClientError()
            return DummyRequestCtx(DummyResp())

    monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **k: DummySession())
    status, data = asyncio.run(sac.fetch_inventory("1"))
    assert status == expected


@pytest.mark.parametrize("status", ["parsed", "incomplete", "private"])
def test_user_template_safe(monkeypatch, status):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BPTF_API_KEY", "x")
    monkeypatch.setattr(
        "utils.price_loader.ensure_prices_cached",
        lambda refresh=False: asyncio.sleep(0, result=Path("prices.json")),
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached",
        lambda refresh=False: asyncio.sleep(0, result=Path("currencies.json")),
    )
    monkeypatch.setattr("utils.price_loader.build_price_map", lambda path: {})
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

    with app.app.test_request_context():
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
    ld.ITEMS_BY_DEFINDEX = {
        9000: {"item_name": "Painted", "image_url": "", "craft_class": "weapon"}
    }
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    monkeypatch.setattr(ld, "PAINT_NAMES", {"3100495": "Test Paint"}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"Test Kit": 350}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Test Kit"}, False)

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
    ld.ITEMS_BY_DEFINDEX = {
        15141: {"item_name": "Flamethrower", "craft_class": "weapon"}
    }
    ld.ITEMS_BY_DEFINDEX[15141]["craft_class"] = "weapon"
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"Warhawk": 350}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["resolved_name"] == "Warhawk Flamethrower"
    assert item["base_weapon"] == "Flamethrower"
    assert item["skin_name"] == "Warhawk"
    assert item["warpaint_id"] == 350
    assert item["warpaint_name"] == "Warhawk"
    assert item["paintkit_name"] == "Warhawk"


def test_warpaint_unknown_defaults_unknown(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15141,
                "quality": 15,
                "attributes": [{"defindex": 834, "float_value": 999}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15141: {"item_name": "Flamethrower", "craft_class": "weapon"}
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["warpaint_id"] == 999
    assert item["warpaint_name"] == "Unknown"


def test_no_warpaint_attribute(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15141,
                "quality": 15,
                "attributes": [],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15141: {"item_name": "Flamethrower", "craft_class": "weapon"}
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"Warhawk": 350}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["warpaint_id"] is None
    assert item["warpaint_name"] is None
    assert item["name"] == "Decorated Weapon Flamethrower"


def test_warpaint_zero_resolves(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15141,
                "quality": 15,
                "attributes": [{"defindex": 834, "value": 0}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15141: {"item_name": "Flamethrower", "craft_class": "weapon"}
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"Red Rock Roscoe": 0}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"0": "Red Rock Roscoe"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["warpaint_id"] == 0
    assert item["warpaint_name"] == "Red Rock Roscoe"


def test_warpaint_invalid_value(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15141,
                "quality": 15,
                "attributes": [{"defindex": 834, "value": "bad"}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15141: {"item_name": "Flamethrower", "craft_class": "weapon"}
    }
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["warpaint_id"] is None
    assert item["warpaint_name"] is None


def test_warpaint_value_preferred_over_float(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15141,
                "quality": 15,
                "attributes": [
                    {"defindex": 834, "value": 350, "float_value": 1},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15141: {"item_name": "Flamethrower", "craft_class": "weapon"}
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"Warhawk": 350}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["warpaint_id"] == 350
    assert item["warpaint_name"] == "Warhawk"
    assert item["resolved_name"] == "Warhawk Flamethrower"
    assert item["skin_name"] == "Warhawk"
    assert item["base_weapon"] == "Flamethrower"
    assert item["skin_name"] == "Warhawk"
    assert item["base_weapon"] == "Flamethrower"
    assert item["resolved_name"] == "Warhawk Flamethrower"


def test_composite_name_set_for_skin(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15141,
                "quality": 15,
                "attributes": [{"defindex": 834, "float_value": 350}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15141: {"item_name": "Flamethrower", "craft_class": "weapon"}
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"Warhawk": 350}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["composite_name"] == "Warhawk Flamethrower"


def test_warpaint_tool_resolved(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 9536,
                "quality": 15,
                "attributes": [{"defindex": 834, "value": 350}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        9536: {
            "item_name": "War Paint",
            "item_class": "tool",
            "tool": {"type": "paintkit"},
        }
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["resolved_name"] == "War Paint: Warhawk"
    assert item["base_weapon"] is None
    assert item["skin_name"] is None


def test_warpaint_tool_resolved_16200(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 16200,
                "quality": 15,
                "attributes": [{"defindex": 834, "value": 350}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        16200: {
            "item_name": "War Paint",
            "item_class": "tool",
            "tool": {"type": "paintkit"},
        }
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["resolved_name"] == "War Paint: Warhawk"
    assert item["base_weapon"] is None
    assert item["skin_name"] is None


def test_warpaint_index_749(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15141,
                "quality": 15,
                "attributes": [
                    {"defindex": 749, "value": 350},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15141: {"item_name": "Flamethrower", "craft_class": "weapon"}
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["warpaint_id"] == 350
    assert item["warpaint_name"] == "Warhawk"


def test_unknown_defindex_preserves_warpaint(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 99999,
                "quality": 15,
                "attributes": [{"defindex": 834, "float_value": 350}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {}
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"Warhawk": 350}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["base_name"].startswith("Unknown Weapon")
    assert item["warpaint_id"] == 350
    assert item["warpaint_name"] == "Warhawk"
    assert item["resolved_name"] == "Warhawk Unknown Weapon"
    assert item["skin_name"] == "Warhawk"
    assert item["base_weapon"] == "Unknown Weapon"


def test_warpaintable_inferred_from_item_class(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 16001,
                "quality": 15,
                "attributes": [{"defindex": 834, "float_value": 350}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        16001: {"item_name": "Tester", "item_class": "tf_weapon_test"}
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"Warhawk": 350}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["warpaint_id"] == 350
    assert item["warpaint_name"] == "Warhawk"
    assert item["skin_name"] == "Warhawk"
    assert item["base_weapon"] == "Tester"
    assert item["resolved_name"] == "Warhawk Tester"


def test_warpaint_resolved_from_schema_name(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15154,
                "quality": 15,
                "attributes": [],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15154: {
            "name": "warbird_sniperrifle_airwolf",
            "item_name": "Sniper Rifle",
            "craft_class": "weapon",
        }
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"Airwolf": 82}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"82": "Airwolf"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["warpaint_id"] == 82
    assert item["warpaint_name"] == "Airwolf"
    assert item["skin_name"] == "Airwolf"
    assert item["base_weapon"] == "Sniper Rifle"
    assert item["resolved_name"] == "Airwolf Sniper Rifle"


def test_warpaint_resolved_from_schema_name_mk_ii(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15155,
                "quality": 15,
                "attributes": [],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15155: {
            "name": "warbird_shotgun_carpet_bomber_mk_ii",
            "item_name": "Boomstick",
            "craft_class": "weapon",
        }
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"Carpet Bomber Mk.II": 104}, False)
    monkeypatch.setattr(
        ld, "PAINTKIT_NAMES_BY_ID", {"104": "Carpet Bomber Mk.II"}, False
    )
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["warpaint_id"] == 104
    assert item["warpaint_name"] == "Carpet Bomber Mk.II"
    assert item["skin_name"] == "Carpet Bomber Mk.II"
    assert item["base_weapon"] == "Boomstick"
    assert item["resolved_name"] == "Carpet Bomber Mk.II Boomstick"


def test_warpaint_resolved_from_schema_name_nutcracker(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15157,
                "quality": 15,
                "attributes": [],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15157: {
            "name": "warbird_rocketlauncher_nutcracker_mk_ii",
            "item_name": "Rocket Launcher",
            "craft_class": "weapon",
        }
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"Nutcracker Mk.II": 161}, False)
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"161": "Nutcracker Mk.II"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["warpaint_id"] == 161
    assert item["warpaint_name"] == "Nutcracker Mk.II"
    assert item["skin_name"] == "Nutcracker Mk.II"
    assert item["base_weapon"] == "Rocket Launcher"
    assert item["resolved_name"] == "Nutcracker Mk.II Rocket Launcher"


def test_warpaint_resolved_with_best_match(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15156,
                "quality": 15,
                "attributes": [],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15156: {
            "name": "warbird_flamethrower_warhak",
            "item_name": "Flamethrower",
            "craft_class": "weapon",
        }
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES", {"Warhawk": 350}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["warpaint_id"] == 350
    assert item["warpaint_name"] == "Warhawk"


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


def test_australium_only_attribute_kept():
    data = {
        "items": [
            {
                "defindex": 12,
                "quality": 6,
                "attributes": [{"defindex": 2027}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {12: {"item_name": "C", "craft_class": "weapon"}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    items = ip.enrich_inventory(data)
    assert len(items) == 1


def test_price_map_applied(patch_valuation):
    data = {"items": [{"defindex": 42, "quality": 6}]}
    ld.ITEMS_BY_DEFINDEX = {42: {"item_name": "Answer", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {("Answer", 6, False, 0, 0): {"value_raw": 5.33, "currency": "metal"}}
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["price"] == price_map[("Answer", 6, False, 0, 0)]
    assert item["price_string"] == "5.33 ref"
    assert item["formatted_price"] == "5.33 ref"


def test_price_map_strange_lookup(patch_valuation):
    data = {"items": [{"defindex": 111, "quality": 11}]}
    ld.ITEMS_BY_DEFINDEX = {111: {"item_name": "Rocket Launcher", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {11: "Strange"}
    price_map = {
        ("Rocket Launcher", 11, False, 0, 0): {"value_raw": 5.33, "currency": "metal"}
    }
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["price"] == price_map[("Rocket Launcher", 11, False, 0, 0)]
    assert item["price_string"] == "5.33 ref"
    assert item["formatted_price"] == "5.33 ref"


def test_price_map_key_conversion_large_value(patch_valuation):
    data = {"items": [{"defindex": 42, "quality": 6}]}
    ld.ITEMS_BY_DEFINDEX = {42: {"item_name": "Answer", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {("Answer", 6, False, 0, 0): {"value_raw": 367.73, "currency": "metal"}}
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 70.0}}}

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["formatted_price"] == "5 Keys 17.73 ref"
    assert item["price_string"] == "5 Keys 17.73 ref"


def test_price_map_unusual_lookup(patch_valuation):
    data = {
        "items": [
            {
                "defindex": 30998,
                "quality": 5,
                "attributes": [{"defindex": 134, "float_value": 13}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {30998: {"item_name": "Veil", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {5: "Unusual"}
    price_map = {
        ("Veil", 5, False, 13, 0): {"value_raw": 164554.25, "currency": "keys"}
    }
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 67.165}}}

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["formatted_price"] == "2449 Keys 67.16 ref"
    assert item["price_string"] == "2449 Keys 67.16 ref"


def test_untradable_item_no_price(patch_valuation):
    data = {"items": [{"defindex": 42, "quality": 6, "tradable": 0}]}
    ld.ITEMS_BY_DEFINDEX = {42: {"item_name": "Answer", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {("Answer", 6, False, 0, 0): {"value_raw": 5.33, "currency": "metal"}}
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert "price" not in item
    assert "price_string" not in item


def test_tradable_item_missing_price(patch_valuation):
    data = {"items": [{"defindex": 43, "quality": 6, "tradable": 1}]}
    ld.ITEMS_BY_DEFINDEX = {43: {"item_name": "Bazooka", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}

    patch_valuation({})
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["price"] is None
    assert item["price_string"] == ""


def test_australium_display_name():
    data = {"items": [{"defindex": 111, "quality": 6, "is_australium": True}]}
    ld.ITEMS_BY_DEFINDEX = {111: {"item_name": "Rocket Launcher", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["name"] == "Australium Rocket Launcher"
    assert item["display_name"] == "Australium Rocket Launcher"


def test_australium_attribute_sets_flag():
    data = {
        "items": [
            {
                "defindex": 111,
                "quality": 6,
                "attributes": [{"defindex": 2027}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {111: {"item_name": "Rocket Launcher", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["is_australium"] is True
    assert item["name"] == "Australium Rocket Launcher"
    assert item["display_name"] == "Australium Rocket Launcher"


def test_price_map_australium_lookup(patch_valuation):
    data = {"items": [{"defindex": 205, "quality": 6, "is_australium": True}]}
    ld.ITEMS_BY_DEFINDEX = {205: {"item_name": "Rocket Launcher", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {
        ("Rocket Launcher", 6, True, 0, 0): {"value_raw": 100.0, "currency": "keys"}
    }
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["price"] == price_map[("Rocket Launcher", 6, True, 0, 0)]
    assert item["formatted_price"] == "2 Keys"


def test_war_paint_tool_attributes(monkeypatch):
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
        5681: {"item_name": "War Paint", "item_class": "tool"},
        222: {"item_name": "Rocket Launcher"},
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["is_war_paint_tool"] is True
    assert item["paintkit_id"] == 350
    assert item["paintkit_name"] == "Warhawk"
    assert item["wear_name"] == "Field-Tested"
    assert item["target_weapon_defindex"] == 222
    assert item["target_weapon_name"] == "Rocket Launcher"
    assert item["resolved_name"] == "War Paint: Warhawk (Field-Tested)"


def test_skin_detection(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15141,
                "quality": 15,
                "attributes": [
                    {"defindex": 834, "value": 350},
                    {"defindex": 749, "float_value": 0.04},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15141: {"item_name": "Flamethrower", "craft_class": "weapon"}
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["is_skin"] is True
    assert item["paintkit_id"] == 350
    assert item["paintkit_name"] == "Warhawk"
    assert item["wear_name"] == "Factory New"
    assert item["resolved_name"] == "Warhawk Flamethrower"


def test_skin_attribute_order(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 15141,
                "quality": 15,
                "attributes": [
                    {"defindex": 749, "float_value": 0.04},
                    {"defindex": 834, "value": 350},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        15141: {"item_name": "Flamethrower", "craft_class": "weapon"}
    }
    monkeypatch.setattr(ld, "PAINTKIT_NAMES_BY_ID", {"350": "Warhawk"}, False)
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["paintkit_id"] == 350
    assert item["wear_name"] == "Factory New"
    assert item["display_name"] == "Warhawk Flamethrower"
    assert item["wear_float"] == 0.04


def test_extract_wear_attr_749(monkeypatch):
    ld.SCHEMA_ATTRIBUTES = {749: {"attribute_class": "texture_wear_default"}}
    asset = {"attributes": [{"defindex": 749, "float_value": 0.04}]}
    wear = ip._extract_wear(asset)
    assert wear == "Factory New"
