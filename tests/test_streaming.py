import importlib
from flask import Response


def test_inventory_chunk_streams(app, monkeypatch):
    mod = importlib.import_module("app")
    monkeypatch.setattr(mod, "CHUNK_SIZE", 1)
    monkeypatch.setattr(
        mod,
        "build_user_data",
        lambda sid: {
            "steamid": sid,
            "items": [{"name": "A", "image_url": ""}, {"name": "B", "image_url": ""}],
            "status": "parsed",
        },
    )
    client = app.test_client()
    resp: Response = client.get("/inventory_chunk/1")
    assert resp.status_code == 200
    assert resp.mimetype == "text/event-stream"
    chunks = list(resp.response)
    assert len(chunks) >= 3
    joined = b"".join(chunks).decode()
    assert "item-wrapper" in joined


def test_index_shows_loading(app):
    client = app.test_client()
    steamid = "76561198034301681"
    resp = client.post("/", data={"steamids": steamid})
    html = resp.get_data(as_text=True)
    assert "Loading inventory" in html
