from utils import inventory_processor as ip
from utils import schema_fetcher as sf
from utils import steam_api_client as sac
import requests


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


def test_fetch_inventory_handles_http_error(monkeypatch, caplog):
    class DummyResp:
        def __init__(self, status):
            self.status_code = status

        def raise_for_status(self):
            raise requests.HTTPError(response=self)

        def json(self):
            return {}

    def fake_get(url, headers=None, timeout=10):
        return DummyResp(400)

    monkeypatch.setattr(sac.requests, "get", fake_get)
    caplog.set_level("WARNING")
    data = ip.fetch_inventory("1")
    assert data == {"assets": [], "descriptions": []}
    assert any(
        "Inventory fetch failed for 1: HTTP 400" in r.message for r in caplog.records
    )


def test_fetch_inventory_marks_incomplete(monkeypatch):
    class DummyResp:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"assets": [{"classid": "1"}]}

    def fake_get(url, headers=None, timeout=20):
        return DummyResp()

    monkeypatch.setattr(sac.requests, "get", fake_get)
    data, status = sac.fetch_inventory("1")
    assert status == "incomplete"
    assert ip.enrich_inventory(data) == []
