import sys
from pathlib import Path
import importlib

import pytest
import pytest_asyncio
from asgiref.wsgi import WsgiToAsgi
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def app(monkeypatch):
    """Return Flask app with env and schema mocks."""

    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BPTF_API_KEY", "x")
    monkeypatch.setattr("utils.local_data.load_files", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(
        "utils.price_loader.ensure_prices_cached",
        lambda refresh=False: Path("prices.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached",
        lambda refresh=False: Path("currencies.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.build_price_map",
        lambda path: {},
    )

    mod = importlib.import_module("app")
    importlib.reload(mod)
    mod.app.secret_key = "test"
    return mod.app


@pytest_asyncio.fixture
async def async_client(app):
    asgi_app = WsgiToAsgi(app)
    transport = httpx.ASGITransport(app=asgi_app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture(autouse=True)
def mock_schema_attrs(monkeypatch):
    """Populate minimal schema attributes for tests."""
    from utils import local_data as ld
    from utils.inventory import extract_attr_classes as eac

    mapping = {
        134: {"name": "paintkit_proto_def_index", "attribute_class": "paintkit_proto_def_index"},
        2041: {"name": "taunt attach particle index", "attribute_class": "taunt_attach_particle_index"},
        2013: {"name": "killstreak effect", "attribute_class": "killstreak_effect"},
        2014: {"name": "killstreak idleeffect", "attribute_class": "killstreak_idleeffect"},
        2025: {"name": "killstreak tier", "attribute_class": "killstreak_tier"},
        142: {"name": "set item tint RGB", "attribute_class": "set_item_tint_rgb"},
        261: {"name": "set item tint RGB 2", "attribute_class": "set_item_tint_rgb"},
        725: {"name": "set_item_texture_wear", "attribute_class": "set_item_texture_wear"},
        749: {"name": "texture_wear_default", "attribute_class": "texture_wear_default"},
        834: {"name": "paintkit_proto_def_index", "attribute_class": "paintkit_proto_def_index"},
        866: {"name": "custom_paintkit_seed_lo", "attribute_class": "custom_paintkit_seed_lo"},
        867: {"name": "custom_paintkit_seed_hi", "attribute_class": "custom_paintkit_seed_hi"},
        187: {"name": "set supply crate series", "attribute_class": "set_supply_crate_series"},
        2053: {"name": "is_festivized", "attribute_class": "is_festivized"},
        214: {"name": "kill eater", "attribute_class": "kill_eater"},
        292: {"name": "kill eater score type", "attribute_class": "kill_eater_score_type"},
        189: {"name": "elevate quality", "attribute_class": "elevate_quality"},
        2028: {"name": "is marketable", "attribute_class": "is_marketable"},
        449: {"name": "never craftable", "attribute_class": "never_craftable"},
        760: {"name": "allow_halloween_offering", "attribute_class": "allow_halloween_offering"},
        2012: {"name": "tool target item", "attribute_class": "tool_target_item"},
    }
    monkeypatch.setattr(ld, "SCHEMA_ATTRIBUTES", mapping, False)
    eac.refresh_attr_classes()
