import importlib
import asyncio


def test_get_home_displays_preloaded_user(async_client, app):
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

    async def run():
        resp = await async_client.get("/")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'id="user-1"' in html

    asyncio.run(run())


def test_post_invalid_ids_flash(async_client):
    async def run():
        resp = await async_client.post("/", data={"steamids": "foobar"})
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert "No valid Steam IDs found!" in html

    asyncio.run(run())


def test_post_valid_ids_sets_initial_ids(async_client):
    async def run():
        steamid = "76561198034301681"
        resp = await async_client.post("/", data={"steamids": steamid})
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert steamid in html
        assert "window.initialIds" in html

    asyncio.run(run())


def test_hidden_items_not_rendered(async_client, app):
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

    async def run():
        resp = await async_client.get("/")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert "Visible" in html
        assert "Hid" not in html

    asyncio.run(run())
