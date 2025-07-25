from utils import inventory_processor as ip
from utils import local_data as ld
from utils.valuation_service import ValuationService
from pathlib import Path
import pytest


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


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["parsed", "incomplete", "private"])
async def test_user_template_safe(monkeypatch, status):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BPTF_API_KEY", "x")
    monkeypatch.setattr(
        "utils.price_loader.ensure_prices_cached",
        lambda refresh=False: Path("prices.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached",
        lambda refresh=False: Path("currencies.json"),
    )
    monkeypatch.setattr("utils.price_loader.build_price_map", lambda path: {})
    monkeypatch.setattr(
        "utils.price_loader.PRICE_MAP_FILE",
        Path("price_map.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.dump_price_map",
        lambda mapping, path=Path("price_map.json"): path,
    )
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

    async with app.app.app_context():
        await app.render_template("_user.html", user=user)


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
        9000: {"item_name": "Painted", "image_url": "", "craft_class": "weapon"},
        5813: {"image_url": "https://example.com/statclock.png"},
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
        "icon_url": "https://example.com/statclock.png",
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


def test_border_color_for_elevated_strange(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 111,
                "quality": 1,
                "attributes": [
                    {"defindex": 214, "value": 5},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {111: {"item_name": "Thing", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {1: "Genuine", 11: "Strange"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["quality"] == "Genuine"
    assert item["strange_count"] == 5
    assert item["border_color"] == ip.QUALITY_MAP[11][1]


def test_border_color_for_strange_unusual(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 222,
                "quality": 5,
                "attributes": [
                    {"defindex": 214, "value": 3},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {222: {"item_name": "Oddity", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {5: "Unusual", 11: "Strange"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["quality"] == "Unusual"
    assert item["strange_count"] == 3
    assert item["border_color"] == ip.QUALITY_MAP[11][1]
    assert item["quality_color"] == ip.QUALITY_MAP[5][1]


def test_border_color_for_strange_collectors(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 333,
                "quality": 14,
                "attributes": [
                    {"defindex": 214, "value": 7},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {333: {"item_name": "Rarity", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {14: "Collector's", 11: "Strange"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["quality"] == "Collector's"
    assert item["strange_count"] == 7
    assert item["border_color"] == ip.QUALITY_MAP[11][1]
    assert item["quality_color"] == ip.QUALITY_MAP[14][1]


def test_plain_craft_weapon_filtered():
    data = {"items": [{"defindex": 10, "quality": 6}]}
    ld.ITEMS_BY_DEFINDEX = {10: {"item_name": "A", "craft_class": "weapon"}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    items = ip.enrich_inventory(data)
    assert items == []


@pytest.mark.parametrize("origin", [1, 5, 14])
def test_plain_craft_weapon_with_special_origin_hidden(origin, patch_valuation):
    data = {
        "items": [
            {"defindex": 10, "quality": 6, "origin": origin, "flag_cannot_trade": True}
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {10: {"item_name": "A", "craft_class": "weapon"}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {("A", 6, True, False, 0, 0): {"value_raw": 1, "currency": "metal"}}
    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    assert len(items) == 1
    item = items[0]
    assert item["_hidden"] is True
    assert "price" not in item
    assert "price_string" not in item


@pytest.mark.parametrize("origin", [1, 5, 14])
def test_plain_craft_weapon_with_special_origin_visible(origin, patch_valuation):
    data = {"items": [{"defindex": 10, "quality": 6, "origin": origin, "tradable": 1}]}
    ld.ITEMS_BY_DEFINDEX = {10: {"item_name": "A", "craft_class": "weapon"}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {("A", 6, True, False, 0, 0): {"value_raw": 1, "currency": "metal"}}
    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    assert len(items) == 1
    item = items[0]
    assert item["_hidden"] is False
    assert item["price"] is not None


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
    price_map = {
        ("Answer", 6, True, False, 0, 0): {"value_raw": 5.33, "currency": "metal"}
    }
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["price"] == price_map[("Answer", 6, True, False, 0, 0)]
    assert item["price_string"] == "5.33 ref"
    assert item["formatted_price"] == "5.33 ref"


def test_price_map_strange_lookup(patch_valuation):
    data = {"items": [{"defindex": 111, "quality": 11}]}
    ld.ITEMS_BY_DEFINDEX = {111: {"item_name": "Rocket Launcher", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {11: "Strange"}
    price_map = {
        ("Rocket Launcher", 11, True, False, 0, 0): {
            "value_raw": 5.33,
            "currency": "metal",
        }
    }
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["price"] == price_map[("Rocket Launcher", 11, True, False, 0, 0)]
    assert item["price_string"] == "5.33 ref"
    assert item["formatted_price"] == "5.33 ref"


def test_price_map_key_conversion_large_value(patch_valuation):
    data = {"items": [{"defindex": 42, "quality": 6}]}
    ld.ITEMS_BY_DEFINDEX = {42: {"item_name": "Answer", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {
        ("Answer", 6, True, False, 0, 0): {"value_raw": 367.73, "currency": "metal"}
    }
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
        ("Veil", 5, True, False, 13, 0): {"value_raw": 164554.25, "currency": "keys"}
    }
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 67.165}}}

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["formatted_price"] == "2449 Keys 67.16 ref"
    assert item["price_string"] == "2449 Keys 67.16 ref"


def test_untradable_item_no_price(patch_valuation):
    data = {"items": [{"defindex": 42, "quality": 6, "flag_cannot_trade": True}]}
    ld.ITEMS_BY_DEFINDEX = {42: {"item_name": "Answer", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {
        ("Answer", 6, True, False, 0, 0): {"value_raw": 5.33, "currency": "metal"}
    }
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert "price" not in item
    assert "price_string" not in item
    assert item["_hidden"] is True


def test_trade_hold_item_priced(patch_valuation):
    data = {
        "items": [
            {
                "defindex": 42,
                "quality": 6,
                "flag_cannot_trade": True,
                "descriptions": [
                    {
                        "value": "Tradable After",
                        "app_data": {"steam_market_tradeable_after": 1752944400},
                    }
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {42: {"item_name": "Answer", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {
        ("Answer", 6, True, False, 0, 0): {"value_raw": 5.33, "currency": "metal"}
    }
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["price"] == price_map[("Answer", 6, True, False, 0, 0)]
    assert item["_hidden"] is False


@pytest.mark.parametrize("tradable_val", [None, 1])
def test_flag_cannot_trade_overrides_tradable(tradable_val, patch_valuation):
    asset = {"defindex": 42, "quality": 6, "flag_cannot_trade": True}
    if tradable_val is not None:
        asset["tradable"] = tradable_val
    data = {"items": [asset]}
    ld.ITEMS_BY_DEFINDEX = {42: {"item_name": "Answer", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {
        ("Answer", 6, True, False, 0, 0): {"value_raw": 5.33, "currency": "metal"}
    }
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert "price" not in item
    assert "price_string" not in item


@pytest.mark.parametrize("origin", [0, 1, 5, 14])
def test_untradable_origin_hidden(origin, patch_valuation):
    data = {
        "items": [
            {"defindex": 44, "quality": 6, "origin": origin, "flag_cannot_trade": True}
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {44: {"item_name": "Widget", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {
        ("Widget", 6, True, False, 0, 0): {"value_raw": 2.0, "currency": "metal"}
    }

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["_hidden"] is True
    assert "price" not in item


def test_untradable_nonlisted_origin_hidden(patch_valuation):
    data = {
        "items": [
            {"defindex": 44, "quality": 6, "origin": 3, "flag_cannot_trade": True}
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {44: {"item_name": "Widget", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {
        ("Widget", 6, True, False, 0, 0): {"value_raw": 2.0, "currency": "metal"}
    }

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["_hidden"] is True
    assert "price" not in item


def test_trade_hold_origin_visible(patch_valuation):
    data = {
        "items": [
            {
                "defindex": 44,
                "quality": 6,
                "origin": 0,
                "flag_cannot_trade": True,
                "descriptions": [
                    {"app_data": {"steam_market_tradeable_after": 1752944400}}
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {44: {"item_name": "Widget", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {
        ("Widget", 6, True, False, 0, 0): {"value_raw": 2.0, "currency": "metal"}
    }

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["_hidden"] is False
    assert item["price"] == price_map[("Widget", 6, True, False, 0, 0)]


@pytest.mark.parametrize("origin", [0, 1, 5, 14])
def test_tradable_origin_visible(origin, patch_valuation):
    data = {"items": [{"defindex": 44, "quality": 6, "origin": origin, "tradable": 1}]}
    ld.ITEMS_BY_DEFINDEX = {44: {"item_name": "Widget", "image_url": ""}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    price_map = {
        ("Widget", 6, True, False, 0, 0): {"value_raw": 2.0, "currency": "metal"}
    }

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["_hidden"] is False
    assert item["price"] is not None


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
        (
            "Rocket Launcher",
            6,
            True,
            True,
            0,
            0,
        ): {"value_raw": 100.0, "currency": "keys"}
    }
    ld.CURRENCIES = {"keys": {"price": {"value_raw": 50.0}}}

    patch_valuation(price_map)
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["price"] == price_map[("Rocket Launcher", 6, True, True, 0, 0)]
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


def test_skin_with_statclock(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 555,
                "quality": 15,
                "attributes": [{"defindex": 214, "value": 42}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        555: {"item_name": "Cool Skin", "image_url": ""},
    }
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon", 11: "Strange"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert "(Strange)" in item["display_name"]
    assert any(b["type"] == "statclock" for b in item["badges"])
    assert item["has_strange_tracking"] is True
    assert item["statclock_badge"] == (
        "http://media.steampowered.com/apps/440/icons/"
        "stattrack.fea7f754b9ab447df18af382036d7d93ed97aca9.png"
    )


def test_decorated_border_color_with_statclock(monkeypatch):
    data = {
        "items": [
            {
                "defindex": 888,
                "quality": 15,
                "attributes": [{"defindex": 214, "value": 99}],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        888: {"item_name": "Fancy Decorated", "image_url": ""},
    }
    ld.QUALITIES_BY_INDEX = {15: "Decorated Weapon", 11: "Strange"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["has_strange_tracking"] is True
    assert item["border_color"] == ip.QUALITY_MAP[11][1]


def test_extract_wear_attr_749(monkeypatch):
    ld.SCHEMA_ATTRIBUTES = {749: {"attribute_class": "texture_wear_default"}}
    asset = {"attributes": [{"defindex": 749, "float_value": 0.04}]}
    wear = ip._extract_wear(asset)
    assert wear == "Factory New"


def test_uncraftable_flag_true():
    data = {"items": [{"defindex": 111, "quality": 6, "flag_cannot_craft": True}]}
    ld.ITEMS_BY_DEFINDEX = {111: {"item_name": "Thing"}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    items = ip.enrich_inventory(data)
    assert items[0]["uncraftable"] is True
    assert items[0]["craftable"] is False


def test_uncraftable_flag_absent():
    data = {"items": [{"defindex": 111, "quality": 6}]}
    ld.ITEMS_BY_DEFINDEX = {111: {"item_name": "Thing"}}
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    items = ip.enrich_inventory(data)
    assert items[0]["uncraftable"] is False
    assert items[0]["craftable"] is True


def test_killstreak_kit_parsing():
    data = {
        "items": [
            {
                "defindex": 6526,
                "quality": 6,
                "attributes": [
                    {"defindex": 2012, "float_value": 36},
                    {"defindex": 2014, "float_value": 2},
                    {"defindex": 2013, "float_value": 2003},
                    {"defindex": 2025, "float_value": 3},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        6526: {"item_name": "Professional Killstreak Kit"},
        36: {"item_name": "Blutsauger", "image_url": "blut.png"},
    }
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    ld.KILLSTREAK_EFFECT_NAMES = {"2003": "Cerebral Discharge"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["target_weapon_defindex"] == 36
    assert item["target_weapon_name"] == "Blutsauger"
    assert item["sheen_name"] == "Deadly Daffodil"
    assert item["killstreak_effect"] == "Cerebral Discharge"
    assert item["killstreak_name"] == "Professional"
    assert item["killstreak_tool_type"] == "kit"
    assert item["fabricator_requirements"] is None
    assert item["stack_key"] is None
    assert item["target_weapon_image"] == "blut.png"


def test_killstreak_fabricator_parsing():
    data = {
        "items": [
            {
                "defindex": 20003,
                "quality": 6,
                "attributes": [
                    {
                        "defindex": 2006,
                        "is_output": True,
                        "itemdef": 6526,
                        "attributes": [
                            {"defindex": 2012, "float_value": 36},
                            {"defindex": 2014, "float_value": 5},
                            {"defindex": 2013, "float_value": 2006},
                            {"defindex": 2025, "float_value": 3},
                        ],
                    },
                    {"defindex": 5706, "itemdef": 5706, "quantity": 3},
                    {"defindex": 5702, "itemdef": 5702, "quantity": 1},
                ],
            }
        ]
    }
    ld.ITEMS_BY_DEFINDEX = {
        20003: {"item_name": "Professional Fabricator"},
        36: {"item_name": "Blutsauger", "image_url": "blut.png"},
        5706: {"item_name": "Battle-Worn Robot KB-808"},
        5702: {"item_name": "Battle-Worn Robot Money Furnace"},
    }
    ld.QUALITIES_BY_INDEX = {6: "Unique"}
    ld.KILLSTREAK_EFFECT_NAMES = {"2006": "Singularity"}
    items = ip.enrich_inventory(data)
    item = items[0]
    assert item["target_weapon_defindex"] == 36
    assert item["target_weapon_name"] == "Blutsauger"
    assert item["sheen_name"] == "Agonizing Emerald"
    assert item["killstreak_effect"] == "Singularity"
    assert item["killstreak_name"] == "Professional"
    assert item["killstreak_tool_type"] == "fabricator"
    assert item["fabricator_requirements"] == [
        {"part": "Battle-Worn Robot KB-808", "qty": 3},
        {"part": "Battle-Worn Robot Money Furnace", "qty": 1},
    ]
    assert item["stack_key"] is None
    assert item["target_weapon_image"] == "blut.png"
