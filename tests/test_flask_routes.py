import importlib
import pytest


@pytest.mark.asyncio
async def test_get_home_displays_preloaded_user(async_client, app):
    mod = importlib.import_module("app")
    user = mod.normalize_user_payload(
        {
            "steamid": "1",
            "avatar": "",
            "username": "Test",
            "playtime": 0,
            "status": "parsed",
            "items": [],
        }
    )
    app.config["PRELOADED_USERS"] = [user]
    app.config["TEST_STEAMID"] = "1"

    resp = await async_client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="user-1"' in html


@pytest.mark.asyncio
async def test_post_invalid_ids_flash(async_client):
    resp = await async_client.post("/", data={"steamids": "foobar"})
    assert resp.status_code == 200
    html = resp.text
    assert (
        "No valid Steam IDs found. Please input in SteamID64, SteamID2, or SteamID3 format."
        in html
    )


@pytest.mark.asyncio
async def test_post_valid_ids_sets_initial_ids(monkeypatch, async_client):
    mod = importlib.import_module("app")

    async def fake_fetch(ids):
        return [f'<div id="user-{i}"></div>' for i in ids], []

    monkeypatch.setattr(mod, "fetch_and_process_many", fake_fetch)
    monkeypatch.setattr(mod.sac, "convert_to_steam64", lambda x: x)

    steamid = "76561198034301681"
    resp = await async_client.post("/", data={"steamids": steamid})
    assert resp.status_code == 200
    html = resp.text
    assert steamid in html
    assert "window.initialIds" in html


@pytest.mark.asyncio
async def test_post_returns_user_cards(monkeypatch, async_client):
    mod = importlib.import_module("app")

    async def fake_fetch(ids):
        return [f'<div id="user-{i}">User {i}</div>' for i in ids], []

    monkeypatch.setattr(mod, "fetch_and_process_many", fake_fetch)
    monkeypatch.setattr(mod.sac, "convert_to_steam64", lambda x: x)

    steamid = "76561198034301681"
    resp = await async_client.post("/", data={"steamids": steamid})
    assert resp.status_code == 200
    html = resp.text
    assert f'id="user-{steamid}"' in html


@pytest.mark.asyncio
async def test_post_mixed_input_ignores_invalid(monkeypatch, async_client):
    mod = importlib.import_module("app")

    captured_ids = []

    async def fake_fetch(ids):
        captured_ids.extend(ids)
        return [f"<div id='user-{i}'></div>" for i in ids], []

    monkeypatch.setattr(mod, "fetch_and_process_many", fake_fetch)
    monkeypatch.setattr(mod.sac, "convert_to_steam64", lambda x: x)

    resp = await async_client.post(
        "/",
        data={"steamids": "STEAM_0:1:4 invalid"},
    )
    assert resp.status_code == 200
    html = resp.text
    assert "user-STEAM_0:1:4" in html
    assert "user-invalid" not in html
    assert captured_ids == ["STEAM_0:1:4"]


@pytest.mark.asyncio
async def test_hidden_items_not_rendered(async_client, app):
    mod = importlib.import_module("app")
    user = mod.normalize_user_payload(
        {
            "steamid": "1",
            "avatar": "",
            "username": "Test",
            "playtime": 0,
            "status": "parsed",
            "items": [
                {"name": "Visible", "image_url": ""},
                {"name": "Hid", "image_url": "", "_hidden": True},
            ],
        }
    )
    app.config["PRELOADED_USERS"] = [user]
    app.config["TEST_STEAMID"] = "1"

    resp = await async_client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "Visible" in html
    assert "Hid" not in html
