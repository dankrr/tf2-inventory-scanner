from utils import constants


def test_api_constants_route(app):
    client = app.test_client()
    resp = client.get("/api/constants")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["paint_colors"]["3100495"][0] == "A Color Similar to Slate"
    assert data["sheen_names"]["1"] == constants.SHEEN_NAMES[1]
    assert (
        data["killstreak_sheen_colors"]["2"][0]
        == constants.KILLSTREAK_SHEEN_COLORS[2][0]
    )
    assert data["killstreak_tiers"]["3"] == constants.KILLSTREAK_TIERS[3]
    assert data["origin_map"]["0"] == constants.ORIGIN_MAP[0]
