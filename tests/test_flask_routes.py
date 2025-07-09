import importlib

import pytest


@pytest.mark.asyncio
async def test_get_home_displays_preloaded_user(test_app):
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
    test_app.config["PRELOADED_USERS"] = [user]
    test_app.config["TEST_STEAMID"] = "1"
    client = test_app.test_client()
    resp = await client.get("/")
    assert resp.status_code == 200
    html = await resp.get_data(as_text=True)
    assert 'id="user-1"' in html


@pytest.mark.asyncio
async def test_post_invalid_ids_flash(test_app):
    client = test_app.test_client()
    resp = await client.post("/", data={"steamids": "foobar"})
    assert resp.status_code == 200
    html = await resp.get_data(as_text=True)
    assert "No valid Steam IDs found!" in html


@pytest.mark.asyncio
async def test_post_valid_ids_sets_initial_ids(test_app):
    client = test_app.test_client()
    steamid = "76561198034301681"
    resp = await client.post("/", data={"steamids": steamid})
    assert resp.status_code == 200
    html = await resp.get_data(as_text=True)
    assert steamid in html
    assert "window.initialIds" in html


@pytest.mark.asyncio
async def test_hidden_items_not_rendered(test_app):
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
    test_app.config["PRELOADED_USERS"] = [user]
    test_app.config["TEST_STEAMID"] = "1"
    client = test_app.test_client()
    resp = await client.get("/")
    assert resp.status_code == 200
    html = await resp.get_data(as_text=True)
    assert "Visible" in html
    assert "Hid" not in html
