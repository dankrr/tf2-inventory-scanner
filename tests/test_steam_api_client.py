import responses
from responses import matchers

from utils import steam_api_client as sac


def test_get_player_summaries(monkeypatch):
    monkeypatch.setattr(sac, "STEAM_API_KEY", "x")
    url = (
        "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
        "?key=x&steamids=1"
    )
    payload = {"response": {"players": [{"steamid": "1", "personaname": "Bob"}]}}
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, url, json=payload, status=200)
        players = sac.get_player_summaries(["1"])
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
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            url,
            json=payload,
            status=200,
            match=[matchers.query_param_matcher(params)],
        )
        hours = sac.get_tf2_playtime_hours("1")
    assert hours == 1.5
