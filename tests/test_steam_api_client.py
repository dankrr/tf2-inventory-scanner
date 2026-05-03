import types
import pytest

from utils import steam_api_client as sac


def test_economy_image_url_helper():
    assert sac._economy_image_url("abc") == f"{sac.ECON_IMAGE_CDN}abc"
    assert sac._economy_image_url("abc", "96fx96f").endswith("abc/96fx96f")
    assert (
        sac._economy_image_url("https://example.com/x.png")
        == "https://example.com/x.png"
    )


def test_steam_cookie_header(monkeypatch):
    monkeypatch.setenv("STEAM_COOKIE_STRING", "a=b; c=d")
    assert sac._steam_cookie_header() == "a=b; c=d"

    monkeypatch.delenv("STEAM_COOKIE_STRING")
    monkeypatch.setenv("STEAM_LOGIN_SECURE", "sec")
    monkeypatch.setenv("STEAM_SESSION_ID", "sid")
    assert sac._steam_cookie_header() == "sessionid=sid; steamLoginSecure=sec"

    monkeypatch.delenv("STEAM_LOGIN_SECURE")
    monkeypatch.delenv("STEAM_SESSION_ID")
    assert sac._steam_cookie_header() is None


@pytest.mark.asyncio
async def test_fetch_inventory_media_async(monkeypatch):
    payload1 = {
        "assets": [{"assetid": "1", "classid": "10", "instanceid": "20"}],
        "descriptions": [
            {
                "classid": "10",
                "instanceid": "20",
                "icon_url": "small",
                "icon_url_large": "large",
                "market_hash_name": "Skin",
            }
        ],
        "more_items": True,
        "last_assetid": "2",
    }
    payload2 = {
        "assets": [{"assetid": "2", "classid": "11", "instanceid": "21"}],
        "descriptions": [
            {"classid": "11", "instanceid": "21", "icon_url": "small2"}
        ],
        "more_items": False,
    }

    calls = []

    class DummyAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, _url, params=None, headers=None):
            calls.append({"params": params, "headers": headers})
            payload = payload1 if len(calls) == 1 else payload2
            return types.SimpleNamespace(status_code=200, json=lambda: payload)

    monkeypatch.setenv("STEAM_COOKIE_STRING", "x=y")
    monkeypatch.setattr(sac.httpx, "AsyncClient", DummyAsyncClient)
    media = await sac.fetch_inventory_media_async("123")
    assert media["1"]["image_url"].endswith("large")
    assert media["2"]["image_url"].endswith("small2")
    assert calls[1]["params"]["start_assetid"] == "2"
    assert "Cookie" in calls[0]["headers"]


@pytest.mark.asyncio
async def test_fetch_inventory_media_async_failure(monkeypatch):
    class DummyAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, *_a, **_k):
            return types.SimpleNamespace(status_code=500, json=lambda: {})

    monkeypatch.setattr(sac.httpx, "AsyncClient", DummyAsyncClient)
    assert await sac.fetch_inventory_media_async("123") == {}


@pytest.mark.asyncio
async def test_fetch_inventory_merges_media(monkeypatch):
    monkeypatch.setattr(sac, "STEAM_API_KEY", "x")
    async def _media(_sid):
        return {
            "999": {
                "image_url": "https://steamcommunity-a.akamaihd.net/economy/image/hash",
                "image_url_small": "small",
                "media_source": "steam_community_inventory",
            }
        }

    monkeypatch.setattr(sac, "fetch_inventory_media_async", _media)

    payload = {"result": {"status": 1, "items": [{"id": "999", "defindex": 1}]}}

    class DummyAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, *_a, **_k):
            return types.SimpleNamespace(json=lambda: payload, status_code=200)

    monkeypatch.setattr(sac.httpx, "AsyncClient", DummyAsyncClient)
    status, result = await sac.fetch_inventory_async("123")
    assert status == "parsed"
    assert result["items"][0]["media_source"] == "steam_community_inventory"
    assert result["items"][0]["image_url_small"] == "small"


@pytest.mark.asyncio
async def test_fetch_inventory_survives_missing_media(monkeypatch):
    monkeypatch.setattr(sac, "STEAM_API_KEY", "x")
    async def _media(_sid):
        return {}

    monkeypatch.setattr(sac, "fetch_inventory_media_async", _media)
    payload = {"result": {"status": 1, "items": [{"id": "1", "defindex": 1}]}}

    class DummyAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, *_a, **_k):
            return types.SimpleNamespace(json=lambda: payload, status_code=200)

    monkeypatch.setattr(sac.httpx, "AsyncClient", DummyAsyncClient)
    status, result = await sac.fetch_inventory_async("123")
    assert status == "parsed"
    assert result["items"][0]["id"] == "1"
