import httpx
import pytest

from utils.cdn_image_resolver import CDNImageResolver, build_market_hash_name
from utils.inventory import api as inventory_api


def test_market_hash_name_builder_variants():
    assert (
        build_market_hash_name(
            is_australium=True,
            is_war_paint_tool=False,
            item_name="Minigun",
            paintkit_name=None,
            wear_name=None,
        )
        == "Strange Australium Minigun"
    )
    assert (
        build_market_hash_name(
            is_australium=False,
            is_war_paint_tool=False,
            item_name="Scattergun",
            paintkit_name="Civic Duty Mk.II",
            wear_name="Factory New",
        )
        == "Civic Duty Mk.II Scattergun (Factory New)"
    )
    assert (
        build_market_hash_name(
            is_australium=False,
            is_war_paint_tool=True,
            item_name="War Paint",
            paintkit_name="Civic Duty Mk.II",
            wear_name="Field-Tested",
        )
        == "Civic Duty Mk.II War Paint (Field-Tested)"
    )


@pytest.mark.asyncio
async def test_resolver_none_on_failures(monkeypatch):
    resolver = CDNImageResolver()

    async def fake_get_404(self, url):
        return httpx.Response(404, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get_404)
    assert await resolver.resolve_hash("x") is None


@pytest.mark.asyncio
async def test_cache_hit_short_circuits(monkeypatch, tmp_path):
    cache_file = tmp_path / "cdn.json"
    cache_file.write_text('{"aus:202":"hash123"}')
    resolver = CDNImageResolver(cache_file)

    async def boom(self, url):
        raise AssertionError("network should not be called")

    monkeypatch.setattr(httpx.AsyncClient, "get", boom)
    item = {"defindex": "202", "is_australium": True}
    url = await resolver.resolve_item_image(item)
    assert "hash123" in url


@pytest.mark.asyncio
async def test_enrich_inventory_variant_patch(monkeypatch):
    async def fake_process(asset, valuation_service=None):
        return asset

    async def fake_resolve(self, item):
        if item.get("is_australium") or item.get("paintkit_id"):
            return "https://community.cloudflare.steamstatic.com/economy/image/hash/360fx360f"
        return None

    monkeypatch.setattr(
        inventory_api, "_process_item", lambda asset, valuation_service=None: asset
    )
    monkeypatch.setattr(CDNImageResolver, "resolve_item_image", fake_resolve)

    data = {
        "items": [
            {
                "name": "Australium Minigun",
                "is_australium": True,
                "defindex": "202",
                "image_url": "stock",
            },
            {
                "name": "Civic Duty Mk.II Scattergun",
                "paintkit_id": 1,
                "wear_id": 1,
                "defindex": "13",
                "image_url": "stock",
            },
            {"name": "Mann Co. Supply Crate Key", "image_url": "key"},
        ]
    }
    items = await inventory_api.enrich_inventory_async(data)
    assert items[0]["image_url"].startswith(
        "https://community.cloudflare.steamstatic.com"
    )
    assert items[1]["image_url"].startswith(
        "https://community.cloudflare.steamstatic.com"
    )
    assert items[2]["image_url"] == "key"
