from utils import inventory_processor as ip
from utils import schema_fetcher as sf
from utils import steam_api_client as sac
import requests
import responses
import pytest


def test_enrich_inventory():
    data = {
        "assets": [{"classid": "1"}],
        "descriptions": [
            {
                "classid": "1",
                "icon_url": "icon.png",
                "app_data": {"def_index": "111"},
            }
        ],
    }
    sf.SCHEMA = {"111": {"defindex": 111, "name": "Test Item", "image_url": "img"}}
    sf.QUALITIES = {}
    items = ip.enrich_inventory(data)
    assert items[0]["name"] == "Test Item"
    assert items[0]["image_url"].startswith(
        "https://community.cloudflare.steamstatic.com/economy/image/"
    )


def test_process_inventory_handles_missing_icon():
    data = {
        "assets": [{"classid": "1"}, {"classid": "2"}],
        "descriptions": [
            {"classid": "1", "icon_url": "icon.png", "app_data": {"def_index": "1"}},
            {"classid": "2", "app_data": {"def_index": "2"}},
        ],
    }
    sf.SCHEMA = {
        "1": {"defindex": 1, "name": "One", "image_url": "a"},
        "2": {"defindex": 2, "name": "Two", "image_url": ""},
    }
    sf.QUALITIES = {}
    items = ip.process_inventory(data)
    assert {i["name"] for i in items} == {"One", "Two"}
    for item in items:
        if item["name"] == "One":
            assert item["image_url"].startswith(
                "https://community.cloudflare.steamstatic.com/economy/image/"
            )
        else:
            assert item["image_url"] == ""


def test_get_inventories_adds_user_agent(monkeypatch):
    captured = {}

    class DummyResp:
        def __init__(self, status=200):
            self.status_code = status

        def raise_for_status(self):
            if self.status_code != 200:
                raise requests.HTTPError(response=self)

        def json(self):
            return {"assets": [], "descriptions": []}

    def fake_get(url, headers=None, timeout=10):
        captured["ua"] = headers.get("User-Agent") if headers else None
        return DummyResp()

    monkeypatch.setattr(sac.requests, "get", fake_get)
    sac.get_inventories(["1"])
    assert captured["ua"] == "Mozilla/5.0"


def test_fetch_inventory_handles_http_error(monkeypatch):
    def fake_fetch(_id):
        return "failed", {}

    monkeypatch.setattr(sac, "fetch_inventory", fake_fetch)
    data, status = ip.fetch_inventory("1")
    assert data == {"assets": [], "descriptions": []}
    assert status == "failed"


@pytest.mark.parametrize(
    "pub_status,key_status,expected",
    [
        ({"status": 200, "json": {"assets": [{"classid": "1"}]}}, None, "parsed"),
        ({"status": 403}, {"status": 200, "json": {"assets": []}}, "private"),
        (
            {"body": requests.ConnectionError()},
            {"body": requests.ConnectionError()},
            "failed",
        ),
    ],
)
def test_fetch_inventory_statuses(monkeypatch, pub_status, key_status, expected):
    monkeypatch.setattr(sac, "STEAM_API_KEY", "x")
    pub_url = "https://steamcommunity.com/inventory/1/440/2?l=en&count=5000"
    key_url = (
        "https://api.steampowered.com/IEconItems_440/GetPlayerItems/v1?key=x&steamid=1"
    )
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, pub_url, **pub_status)
        if key_status is not None:
            rsps.add(responses.GET, key_url, **key_status)
        status, data = sac.fetch_inventory("1")
    assert status == expected
