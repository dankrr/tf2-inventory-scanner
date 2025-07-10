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
