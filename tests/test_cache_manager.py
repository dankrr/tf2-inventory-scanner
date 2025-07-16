from pathlib import Path

import pytest

import utils.cache_manager as cm


def test_missing_cache_files(tmp_path, monkeypatch):
    f1 = tmp_path / "a.json"
    f2 = tmp_path / "b.json"
    f1.write_text("{}")
    monkeypatch.setattr(cm, "REQUIRED_FILES", [f1, f2])
    missing = cm.missing_cache_files()
    assert missing == [f2]


@pytest.mark.asyncio
async def test_fetch_missing_success(monkeypatch, capsys):
    calls = {"refresh": 0}
    missing = [Path("x")]

    monkeypatch.setenv("CACHE_RETRIES", "3")
    monkeypatch.setenv("CACHE_DELAY", "0")
    monkeypatch.setattr(cm, "REQUIRED_FILES", missing)

    def fake_missing():
        return missing

    async def fake_refresh():
        calls["refresh"] += 1
        missing.clear()

    monkeypatch.setattr(cm, "missing_cache_files", fake_missing)
    monkeypatch.setattr(cm, "_do_refresh", fake_refresh)

    ok = await cm.fetch_missing_cache_files()
    out = capsys.readouterr().out
    assert "\x1b[33m🟡 [1/1] Fetching x...\x1b[0m" in out
    assert "\x1b[32m✅ [1/1] x downloaded successfully\x1b[0m" in out
    assert ok is True
    assert calls["refresh"] == 1


@pytest.mark.asyncio
async def test_fetch_missing_failure(monkeypatch, capsys):
    calls = {"refresh": 0}
    missing = [Path("x")]

    monkeypatch.setenv("CACHE_RETRIES", "3")
    monkeypatch.setenv("CACHE_DELAY", "0")
    monkeypatch.setattr(cm, "REQUIRED_FILES", missing)

    def fake_missing():
        return missing

    async def fake_refresh():
        calls["refresh"] += 1

    monkeypatch.setattr(cm, "missing_cache_files", fake_missing)
    monkeypatch.setattr(cm, "_do_refresh", fake_refresh)

    ok = await cm.fetch_missing_cache_files()
    out = capsys.readouterr().out
    assert "\x1b[31m" in out
    assert "Failed after 3 retries" in out
    assert ok is False
    assert calls["refresh"] == 3
