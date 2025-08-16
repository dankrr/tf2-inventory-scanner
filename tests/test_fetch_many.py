import importlib
import asyncio
import time
import pytest


@pytest.mark.asyncio
async def test_fetch_many_concurrent(monkeypatch, app):
    mod = importlib.import_module("app")

    async def fake_build(id_):
        await asyncio.sleep(0.05)
        return {
            "steamid": id_,
            "avatar": "",
            "username": id_,
            "playtime": 0,
            "status": "parsed",
            "items": [],
        }

    monkeypatch.setattr(mod, "build_user_data_async", fake_build)

    with app.test_request_context():
        start = time.perf_counter()
        completed, failed, failed_ids = await mod.fetch_and_process_many(
            ["1", "2", "3"]
        )
        duration = time.perf_counter() - start
    assert len(completed) == 3
    assert failed == []
    assert failed_ids == []
    assert duration < 0.15


@pytest.mark.asyncio
async def test_api_users_returns_html(monkeypatch, async_client):
    mod = importlib.import_module("app")

    async def fake_fetch(ids):
        return [f"<div>{i}</div>" for i in ids], [], []

    monkeypatch.setattr(mod, "fetch_and_process_many", fake_fetch)

    monkeypatch.setattr(mod.sac, "convert_to_steam64", lambda x: x)

    resp = await async_client.post("/api/users", json={"ids": ["1", "2"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"completed": ["<div>1</div>", "<div>2</div>"], "failed": []}


@pytest.mark.asyncio
async def test_fetch_many_deduplicates(monkeypatch, app):
    mod = importlib.import_module("app")

    calls = []

    async def fake_build(id_):
        calls.append(id_)
        return {
            "steamid": id_,
            "avatar": "",
            "username": id_,
            "playtime": 0,
            "status": "parsed",
            "items": [],
        }

    monkeypatch.setattr(mod, "build_user_data_async", fake_build)

    with app.test_request_context():
        completed, failed, failed_ids = await mod.fetch_and_process_many(
            [
                "1",
                "1",
                "2",
                "2",
            ]
        )

    assert len(completed) == 2
    assert failed == []
    assert failed_ids == []
    assert calls == ["1", "2"]
