import utils.steam_api_client as client


def test_convert_steamid2():
    assert client.convert_to_steam64("STEAM_0:1:123456") == "76561197960512641"


def test_convert_steamid3():
    assert client.convert_to_steam64("[U:1:246913]") == "76561197960512641"


def test_convert_steamid64():
    assert client.convert_to_steam64("76561197960512641") == "76561197960512641"


def test_invalid_returns_none():
    assert client.convert_to_steam64("not_an_id") is None
