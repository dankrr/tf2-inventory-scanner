import types
import pytest

from utils import steam_api_client as sac


@pytest.mark.asyncio
async def test_get_player_summaries(monkeypatch):
    monkeypatch.setattr(sac, "STEAM_API_KEY", "x")
    payload = {"response": {"players": [{"steamid": "1", "personaname": "Bob"}]}}

    class DummyAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, *_a, **_k):
            return types.SimpleNamespace(
                json=lambda: payload,
                status_code=200,
                raise_for_status=lambda: None,
            )

    monkeypatch.setattr(sac.httpx, "AsyncClient", DummyAsyncClient)
    players = await sac.get_player_summaries_async(["1"])
    assert players == payload["response"]["players"]


@pytest.mark.asyncio
async def test_get_tf2_playtime_hours(monkeypatch):
    monkeypatch.setattr(sac, "STEAM_API_KEY", "x")
    payload = {"response": {"games": [{"appid": 440, "playtime_forever": 90}]}}

    class DummyAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, *_a, **_k):
            return types.SimpleNamespace(
                json=lambda: payload,
                status_code=200,
                raise_for_status=lambda: None,
            )

    monkeypatch.setattr(sac.httpx, "AsyncClient", DummyAsyncClient)
    hours = await sac.get_tf2_playtime_hours_async("1")
    assert hours == 1.5


def test_convert_vanity_to_steam64(monkeypatch):
    monkeypatch.setattr(sac, "STEAM_API_KEY", "x")

    class DummyClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, *_a, **_k):
            return types.SimpleNamespace(
                status_code=200,
                json=lambda: {
                    "response": {"success": 1, "steamid": "76561197960287930"}
                },
            )

    monkeypatch.setattr(sac.httpx, "Client", DummyClient)
    assert sac.convert_to_steam64("gaben") == "76561197960287930"


@pytest.mark.asyncio
async def test_fetch_inventory_media_async_paginates(monkeypatch):
    pages = [
        {
            "assets": [{"assetid": "1", "classid": "10", "instanceid": "0"}],
            "descriptions": [{"classid": "10", "instanceid": "0", "icon_url": "abc"}],
            "more_items": 1,
            "last_assetid": "1",
        },
        {
            "assets": [{"assetid": "2", "classid": "20", "instanceid": "0"}],
            "descriptions": [
                {"classid": "20", "instanceid": "0", "icon_url_large": "def"}
            ],
            "more_items": 0,
        },
    ]

    class DummyAsyncClient:
        def __init__(self, *a, **k):
            self.calls = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, *_a, **_k):
            payload = pages[self.calls]
            self.calls += 1
            return types.SimpleNamespace(status_code=200, json=lambda: payload)

    monkeypatch.setattr(sac.httpx, "AsyncClient", DummyAsyncClient)
    media = await sac.fetch_inventory_media_async("123")
    assert media["1"]["image_url"] == sac.ECON_IMAGE_CDN + "abc"
    assert media["1"]["image_url_small"] == sac.ECON_IMAGE_CDN + "abc/96fx96f"
    assert media["2"]["image_url"] == sac.ECON_IMAGE_CDN + "def"


@pytest.mark.asyncio
async def test_fetch_inventory_async_media_failure_does_not_fail_inventory(monkeypatch):
    monkeypatch.setattr(sac, "STEAM_API_KEY", "x")

    payload = {"result": {"status": 1, "items": [{"id": "99", "defindex": 1}]}}

    class DummyAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, *_a, **_k):
            return types.SimpleNamespace(status_code=200, json=lambda: payload)

    async def _boom(_steamid):
        return {}

    monkeypatch.setattr(sac.httpx, "AsyncClient", DummyAsyncClient)
    monkeypatch.setattr(sac, "fetch_inventory_media_async", _boom)

    status, result = await sac.fetch_inventory_async("123")
    assert status == "parsed"
    assert result["items"][0]["id"] == "99"
