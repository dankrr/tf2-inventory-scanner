import inventory_scanner
import pytest


class DummyResp:
    def raise_for_status(self):
        pass

    def json(self):
        return {"result": {"items": [{"defindex": 1, "quality": 6}]}}


def test_main_usage(capsys):
    with pytest.raises(SystemExit) as exc:
        inventory_scanner.main([])
    out = capsys.readouterr().out
    assert "Usage" in out
    assert exc.value.code == 1


def test_main_prints_item_count(monkeypatch, capsys):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setattr(
        inventory_scanner.requests, "get", lambda url, timeout=10: DummyResp()
    )
    inventory_scanner.main(["123"])
    out = capsys.readouterr().out
    assert "Found 1 items in inventory for 123" in out


def test_refresh_schema(monkeypatch, capsys):
    called = {"refresh": None}

    def fake_refresh(self, verbose: bool = False):
        called["refresh"] = verbose
        if verbose:
            print("schema/items.json - 0 entries")

    monkeypatch.setattr(inventory_scanner.SchemaProvider, "refresh_all", fake_refresh)
    inventory_scanner.main(["--refresh"])
    out = capsys.readouterr().out
    assert "Schema refreshed" in out
    assert "schema/items.json - 0 entries" in out
    assert called["refresh"] is True
