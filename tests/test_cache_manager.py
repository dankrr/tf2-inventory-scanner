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
        return 5

    monkeypatch.setattr(cm, "missing_cache_files", fake_missing)
    monkeypatch.setattr(cm, "_do_refresh", fake_refresh)

    ok = await cm.fetch_missing_cache_files()
    out = capsys.readouterr().out
    assert "\x1b[33m🟡 [1/1] Fetching x...\x1b[0m" in out
    assert "\x1b[32m✅ [1/1] x downloaded successfully\x1b[0m" in out
    assert "1 missing files fetched" in out
    assert "4 extra schema" in out
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


@pytest.mark.asyncio
async def test_skip_cache(monkeypatch, capsys):
    monkeypatch.setenv("SKIP_CACHE_INIT", "1")
    ok = await cm.fetch_missing_cache_files()
    out = capsys.readouterr().out
    assert "\u26A0" in out
    assert ok is True


@pytest.mark.asyncio
async def test_retry_note(monkeypatch, capsys):
    monkeypatch.setenv("CACHE_RETRIES", "4")
    monkeypatch.setenv("CACHE_DELAY", "1")

    monkeypatch.setattr(cm, "missing_cache_files", lambda: [])

    ok = await cm.fetch_missing_cache_files()
    out = capsys.readouterr().out
    assert "Retrying up to 4 times with 1 sec delay" in out
    assert ok is True
