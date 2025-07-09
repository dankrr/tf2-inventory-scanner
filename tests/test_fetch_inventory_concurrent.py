import importlib
import queue


def test_retry_prevents_duplicate_failures(monkeypatch):
    mod = importlib.import_module("app")

    call = {"count": 0}

    def fake_build_user_data(sid: str):
        call["count"] += 1
        return {
            "steamid": sid,
            "username": "u",
            "avatar": "",
            "playtime": 0,
            "items": [],
            "status": "incomplete",
        }

    monkeypatch.setattr(mod, "build_user_data", fake_build_user_data)
    monkeypatch.setattr(mod, "fetch_queue", queue.Queue())

    results, failed = mod.fetch_inventory_concurrently(
        ["1"], max_workers=1, max_retries=1
    )
    assert failed == []
    assert results == []
    assert call["count"] == 1


def test_retry_success_no_duplicate(monkeypatch):
    mod = importlib.import_module("app")

    call = {"count": 0}

    def fake_build_user_data(sid: str):
        call["count"] += 1
        status = "incomplete" if call["count"] == 1 else "parsed"
        return {
            "steamid": sid,
            "username": "u",
            "avatar": "",
            "playtime": 0,
            "items": [],
            "status": status,
        }

    monkeypatch.setattr(mod, "build_user_data", fake_build_user_data)
    monkeypatch.setattr(mod, "fetch_queue", queue.Queue())

    results, failed = mod.fetch_inventory_concurrently(
        ["2"], max_workers=1, max_retries=1
    )
    assert failed == []
    assert results == []
    assert call["count"] == 1


def test_duplicate_ids_processed_once(monkeypatch):
    mod = importlib.import_module("app")

    call = {"count": 0}

    def fake_build_user_data(sid: str):
        call["count"] += 1
        return {
            "steamid": sid,
            "username": "u",
            "avatar": "",
            "playtime": 0,
            "items": [],
            "status": "parsed",
        }

    monkeypatch.setattr(mod, "build_user_data", fake_build_user_data)
    monkeypatch.setattr(mod, "fetch_queue", queue.Queue())

    results, failed = mod.fetch_inventory_concurrently(
        [
            "3",
            "3",
            "3",
        ],
        max_workers=2,
    )

    assert failed == []
    assert [u.steamid for u in results] == ["3"]
    assert call["count"] == 1
