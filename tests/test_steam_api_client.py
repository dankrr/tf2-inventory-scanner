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


def test_extract_steam_ids(monkeypatch):
    async def fake_convert(token: str) -> str:
        mapping = {
            "STEAM_0:0:88939219": "76561198138144166",
            "[U:1:1110742403]": "76561199071008131",
            "[U:1:99950348]": "76561198060216076",
        }
        return mapping.get(token, token)

    async def fake_resolve(slug: str) -> str:
        return {
            "foo": "76561198000000000",
        }[slug]

    monkeypatch.setattr(sac, "convert_to_steam64", fake_convert)
    monkeypatch.setattr(sac, "resolve_vanity_url", fake_resolve)

    text = """
    #    354 "AnonyMouse"        [U:1:1110742403]
    76561198881990960
    STEAM_0:0:88939219
    somename
    [U:1:99950348]
    https://steamcommunity.com/id/foo
    anotherusername
    """

    ids = asyncio.run(sac.extract_steam_ids(text))
    assert ids == [
        "76561199071008131",
        "76561198881990960",
        "76561198138144166",
        "76561198060216076",
        "76561198000000000",
    ]


def test_extract_steam_ids_with_vanity(monkeypatch):
    async def fake_convert(token: str) -> str:
        mapping = {
            "STEAM_0:1:1": "76561197960265731",
            "[U:1:2]": "76561197960265730",
        }
        return mapping.get(token, token)

    async def fake_resolve(slug: str) -> str:
        return {
            "foo": "76561198000000000",
        }[slug]

    monkeypatch.setattr(sac, "convert_to_steam64", fake_convert)
    monkeypatch.setattr(sac, "resolve_vanity_url", fake_resolve)

    text = "STEAM_0:1:1 foo [U:1:2] https://steamcommunity.com/id/foo"
    ids = asyncio.run(sac.extract_steam_ids(text))
    assert ids == ["76561197960265731", "76561197960265730", "76561198000000000"]


def test_extract_ids_status_sebektam():
    text = """
    hostname: s
    # userid name uniqueid connected ping loss state
    #   1 \"Sebektam\" [U:1:921725235] 00:01 50 0 active
    """
    ids = asyncio.run(sac.extract_steam_ids(text))
    assert ids == ["76561198881990963"]
