import asyncio
import aiohttp

from utils import steam_api_client as sac


def test_get_player_summaries(monkeypatch):
    monkeypatch.setattr(sac, "STEAM_API_KEY", "x")
    url = (
        "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
        "?key=x&steamids=1"
    )
    payload = {"response": {"players": [{"steamid": "1", "personaname": "Bob"}]}}

    class DummyResp:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def raise_for_status(self):
            pass

        async def json(self):
            return payload

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
            return DummyRequestCtx(DummyResp())

    monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **k: DummySession())
    players = asyncio.run(sac.get_player_summaries(["1"]))
    assert players == payload["response"]["players"]


def test_get_tf2_playtime_hours(monkeypatch):
    monkeypatch.setattr(sac, "STEAM_API_KEY", "x")
    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    params = {
        "key": "x",
        "steamid": "1",
        "include_played_free_games": 1,
        "format": "json",
    }
    payload = {"response": {"games": [{"appid": 440, "playtime_forever": 90}]}}

    class DummyResp:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def raise_for_status(self):
            pass

        async def json(self):
            return payload

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
            assert kwargs.get("params") == params
            return DummyRequestCtx(DummyResp())

    monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **k: DummySession())
    hours = asyncio.run(sac.get_tf2_playtime_hours("1"))
    assert hours == 1.5
