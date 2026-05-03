"""Tests for CDN image resolver and cache."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from utils.cdn_image_resolver import (
    build_market_hash_name,
    cdn_url,
    is_resolver_enabled,
    resolve_icon_hash,
)
import utils.cdn_image_cache as cache_mod


# ---------------------------------------------------------------------------
# build_market_hash_name
# ---------------------------------------------------------------------------


class TestBuildMarketHashName:
    def test_australium_minigun(self):
        result = build_market_hash_name(is_australium=True, base_name="Minigun")
        assert result == "Strange Australium Minigun"

    def test_australium_strips_strange_prefix(self):
        result = build_market_hash_name(is_australium=True, base_name="Strange Minigun")
        assert result == "Strange Australium Minigun"

    def test_australium_strips_unique_prefix(self):
        result = build_market_hash_name(
            is_australium=True, base_name="Unique Scattergun"
        )
        assert result == "Strange Australium Scattergun"

    def test_war_painted_weapon_factory_new(self):
        result = build_market_hash_name(
            paintkit_name="Civic Duty Mk.II",
            base_name="Scattergun",
            wear_name="Factory New",
        )
        assert result == "Civic Duty Mk.II Scattergun (Factory New)"

    def test_war_paint_tool_field_tested(self):
        result = build_market_hash_name(
            is_war_paint_tool=True,
            paintkit_name="Civic Duty Mk.II",
            wear_name="Field-Tested",
        )
        assert result == "Civic Duty Mk.II War Paint (Field-Tested)"

    def test_plain_item_returns_none(self):
        result = build_market_hash_name(base_name="Mann Co. Supply Crate Key")
        assert result is None

    def test_australium_missing_base_name_returns_none(self):
        result = build_market_hash_name(is_australium=True)
        assert result is None

    def test_war_paint_tool_missing_wear_returns_none(self):
        result = build_market_hash_name(
            is_war_paint_tool=True, paintkit_name="Civic Duty Mk.II"
        )
        assert result is None

    def test_war_painted_missing_wear_returns_none(self):
        result = build_market_hash_name(
            paintkit_name="Civic Duty Mk.II", base_name="Scattergun"
        )
        assert result is None


# ---------------------------------------------------------------------------
# cdn_url
# ---------------------------------------------------------------------------


def test_cdn_url_format():
    url = cdn_url("abc123hash")
    assert (
        url
        == "https://community.cloudflare.steamstatic.com/economy/image/abc123hash/360fx360f"
    )


# ---------------------------------------------------------------------------
# is_resolver_enabled
# ---------------------------------------------------------------------------


def test_resolver_enabled_default(monkeypatch):
    monkeypatch.delenv("CDN_RESOLVER_ENABLED", raising=False)
    assert is_resolver_enabled() is True


def test_resolver_disabled_via_env(monkeypatch):
    monkeypatch.setenv("CDN_RESOLVER_ENABLED", "0")
    assert is_resolver_enabled() is False


def test_resolver_enabled_explicit(monkeypatch):
    monkeypatch.setenv("CDN_RESOLVER_ENABLED", "1")
    assert is_resolver_enabled() is True


# ---------------------------------------------------------------------------
# resolve_icon_hash
# ---------------------------------------------------------------------------

_FAKE_ICON = "fake_icon_hash_abc123"
_FAKE_RENDER_RESPONSE = {
    "assets": {
        "440": {
            "2": {
                "12345": {
                    "icon_url": _FAKE_ICON,
                    "name": "Some Item",
                }
            }
        }
    }
}


@pytest.mark.asyncio
async def test_resolve_icon_hash_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value=_FAKE_RENDER_RESPONSE)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    result = await resolve_icon_hash(mock_client, "Strange Australium Minigun")
    assert result == _FAKE_ICON


@pytest.mark.asyncio
async def test_resolve_icon_hash_404_returns_none():
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    result = await resolve_icon_hash(mock_client, "Nonexistent Item")
    assert result is None


@pytest.mark.asyncio
async def test_resolve_icon_hash_429_returns_none():
    mock_resp = MagicMock()
    mock_resp.status_code = 429

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    result = await resolve_icon_hash(mock_client, "Rate Limited Item")
    assert result is None


@pytest.mark.asyncio
async def test_resolve_icon_hash_network_error_returns_none():
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    result = await resolve_icon_hash(mock_client, "Unreachable Item")
    assert result is None


@pytest.mark.asyncio
async def test_resolve_icon_hash_empty_assets_returns_none():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value={"assets": {}})

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    result = await resolve_icon_hash(mock_client, "Item Without Assets")
    assert result is None


# ---------------------------------------------------------------------------
# Cache hit short-circuits the network call
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_hit_no_network_call(tmp_path, monkeypatch):
    """When the cache already has the hash, no HTTP call should be made."""
    monkeypatch.setenv("CDN_RESOLVER_ENABLED", "1")

    # Override the cache file path and reset state
    monkeypatch.setattr(cache_mod, "CDN_IMAGES_FILE", tmp_path / "cdn_images.json")
    cache_mod._cache.clear()
    cache_mod._loaded = False

    # Seed the cache directly
    cache_mod.put("aus:202", _FAKE_ICON)

    from utils.inventory import api as inv_api
    from utils import local_data as ld

    saved_items_map = ld.ITEMS_BY_DEFINDEX.copy()
    saved_quals = ld.QUALITIES_BY_INDEX.copy()

    ld.ITEMS_BY_DEFINDEX = {
        202: {
            "name": "Minigun",
            "item_name": "Minigun",
            "image_url": "http://example.com/plain_minigun.png",
        }
    }
    ld.QUALITIES_BY_INDEX = {11: "Strange"}

    data = {
        "items": [
            {
                "defindex": 202,
                "quality": 11,
                "attributes": [
                    {"defindex": 2027, "float_value": 1},  # australium flag
                ],
            }
        ]
    }

    http_mock = AsyncMock()
    http_mock.__aenter__ = AsyncMock(return_value=http_mock)
    http_mock.__aexit__ = AsyncMock(return_value=False)

    try:
        with patch("httpx.AsyncClient", return_value=http_mock):
            items = await inv_api.enrich_inventory_async(data)
    finally:
        ld.ITEMS_BY_DEFINDEX = saved_items_map
        ld.QUALITIES_BY_INDEX = saved_quals

    australium_items = [i for i in items if i.get("is_australium")]
    assert australium_items, "Expected at least one australium item"
    item = australium_items[0]
    expected_url = cdn_url(_FAKE_ICON)
    assert item["image_url"] == expected_url

    # Confirm no HTTP call was made (cache hit)
    http_mock.get.assert_not_called()


# ---------------------------------------------------------------------------
# Integration: enrich_inventory_async patches image_url for variants
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enrich_inventory_async_resolves_australium(tmp_path, monkeypatch):
    """Australium items get a CDN image URL; plain items are unchanged."""
    monkeypatch.setenv("CDN_RESOLVER_ENABLED", "1")

    monkeypatch.setattr(cache_mod, "CDN_IMAGES_FILE", tmp_path / "cdn_images.json")
    cache_mod._cache.clear()
    cache_mod._loaded = False

    from utils.inventory import api as inv_api
    from utils import local_data as ld

    saved_items_map = ld.ITEMS_BY_DEFINDEX.copy()
    saved_quals = ld.QUALITIES_BY_INDEX.copy()

    ld.ITEMS_BY_DEFINDEX = {
        202: {
            "name": "Minigun",
            "item_name": "Minigun",
            "image_url": "http://example.com/plain_minigun.png",
        },
        5021: {
            "name": "Mann Co. Supply Crate Key",
            "item_name": "Mann Co. Supply Crate Key",
            "image_url": "http://example.com/key.png",
        },
    }
    ld.QUALITIES_BY_INDEX = {6: "Unique", 11: "Strange"}

    data = {
        "items": [
            {
                "defindex": 202,
                "quality": 11,
                "attributes": [
                    {"defindex": 2027, "float_value": 1},  # australium flag
                ],
            },
            {
                "defindex": 5021,
                "quality": 6,
                "attributes": [],
            },
        ]
    }

    resolved_icon = "resolved_australium_icon_hash"
    render_response = {"assets": {"440": {"2": {"99999": {"icon_url": resolved_icon}}}}}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value=render_response)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    try:
        with patch("httpx.AsyncClient", return_value=mock_client):
            items = await inv_api.enrich_inventory_async(data)
    finally:
        ld.ITEMS_BY_DEFINDEX = saved_items_map
        ld.QUALITIES_BY_INDEX = saved_quals

    by_def = {int(i["defindex"]): i for i in items}

    # Australium Minigun should have CDN URL
    assert 202 in by_def
    assert by_def[202]["image_url"] == cdn_url(resolved_icon)
    assert "steamstatic.com" in by_def[202]["image_url"]

    # Plain key should be unchanged
    assert 5021 in by_def
    assert by_def[5021]["image_url"] == "http://example.com/key.png"


@pytest.mark.asyncio
async def test_enrich_inventory_async_disabled(tmp_path, monkeypatch):
    """When CDN_RESOLVER_ENABLED=0, image_url is unchanged for all items."""
    monkeypatch.setenv("CDN_RESOLVER_ENABLED", "0")

    monkeypatch.setattr(cache_mod, "CDN_IMAGES_FILE", tmp_path / "cdn_images.json")
    cache_mod._cache.clear()
    cache_mod._loaded = False

    from utils.inventory import api as inv_api
    from utils import local_data as ld

    saved_items_map = ld.ITEMS_BY_DEFINDEX.copy()
    saved_quals = ld.QUALITIES_BY_INDEX.copy()

    ld.ITEMS_BY_DEFINDEX = {
        202: {
            "name": "Minigun",
            "item_name": "Minigun",
            "image_url": "http://example.com/plain_minigun.png",
        }
    }
    ld.QUALITIES_BY_INDEX = {11: "Strange"}

    data = {
        "items": [
            {
                "defindex": 202,
                "quality": 11,
                "attributes": [
                    {"defindex": 2027, "float_value": 1},
                ],
            }
        ]
    }

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    try:
        with patch("httpx.AsyncClient", return_value=mock_client):
            items = await inv_api.enrich_inventory_async(data)
    finally:
        ld.ITEMS_BY_DEFINDEX = saved_items_map
        ld.QUALITIES_BY_INDEX = saved_quals

    australium_items = [i for i in items if i.get("is_australium")]
    # Image URL should remain the plain schema URL when resolver is disabled
    for item in australium_items:
        assert "steamstatic.com/economy/image" not in item.get("image_url", "")

    mock_client.get.assert_not_called()


# ---------------------------------------------------------------------------
# cdn_image_cache module tests
# ---------------------------------------------------------------------------


def test_cache_put_and_get(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CDN_IMAGES_FILE", tmp_path / "cdn_images.json")
    cache_mod._cache.clear()
    cache_mod._loaded = False

    assert cache_mod.get("aus:202") is None
    cache_mod.put("aus:202", "some_hash")
    assert cache_mod.get("aus:202") == "some_hash"

    # Verify persisted to disk
    data = json.loads((tmp_path / "cdn_images.json").read_text())
    assert data["aus:202"] == "some_hash"


def test_cache_load_from_disk(tmp_path, monkeypatch):
    cache_file = tmp_path / "cdn_images.json"
    cache_file.write_text(json.dumps({"wpt:10:3": "hash_from_disk"}))

    monkeypatch.setattr(cache_mod, "CDN_IMAGES_FILE", cache_file)
    cache_mod._cache.clear()
    cache_mod._loaded = False

    assert cache_mod.get("wpt:10:3") == "hash_from_disk"


def test_cache_clear(tmp_path, monkeypatch):
    cache_file = tmp_path / "cdn_images.json"
    monkeypatch.setattr(cache_mod, "CDN_IMAGES_FILE", cache_file)
    cache_mod._cache.clear()
    cache_mod._loaded = False

    cache_mod.put("aus:100", "hash1")
    assert cache_file.exists()

    cache_mod.clear()
    assert not cache_file.exists()
    assert cache_mod.get("aus:100") is None


def test_cache_key_helpers():
    assert cache_mod.cache_key_australium(202) == "aus:202"
    assert cache_mod.cache_key_war_painted(200, 10, 2) == "wp:200:10:2"
    assert cache_mod.cache_key_war_paint_tool(10, 3) == "wpt:10:3"
