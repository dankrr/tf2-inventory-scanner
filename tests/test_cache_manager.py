from pathlib import Path

import pytest

import utils.cache_manager as cm


def test_missing_cache_files(tmp_path, monkeypatch):
    f1 = tmp_path / "a.json"
    f2 = tmp_path / "b.json"
    f1.write_text("{}")
    monkeypatch.setattr(cm, "REQUIRED_FILES", [f1, f2])
    missing = cm.missing_cache_files()
    assert missing == [f1, f2]


@pytest.mark.asyncio
async def test_schema_only_refresh(monkeypatch, capsys):
    missing = [Path("cache/schema/items.json")]
    called = {"schema": 0, "prices": 0, "curr": 0}

    monkeypatch.setenv("CACHE_RETRIES", "1")
    monkeypatch.setenv("CACHE_DELAY", "0")
    monkeypatch.setattr(cm, "REQUIRED_FILES", missing)

    monkeypatch.setattr(cm, "missing_cache_files", lambda: missing)

    async def fake_schema():
        called["schema"] += 1
        missing.clear()

    monkeypatch.setattr(cm, "_refresh_schema_concurrent", fake_schema)
    monkeypatch.setattr(
        cm,
        "ensure_prices_cached_async",
        lambda refresh=True: called.__setitem__("prices", 1),
    )
    monkeypatch.setattr(
        cm,
        "ensure_currencies_cached_async",
        lambda refresh=True: called.__setitem__("curr", 1),
    )

    ok, refreshed, schema_ref = await cm.fetch_missing_cache_files()
    out = capsys.readouterr().out
    assert ok is True and refreshed is True and schema_ref is True
    assert called["schema"] == 1
    assert called["prices"] == 0
    assert called["curr"] == 0
    assert "Cache ready" in out


@pytest.mark.asyncio
async def test_pricing_only_refresh(monkeypatch):
    missing = [Path("cache/prices.json")]
    called = {"schema": 0, "prices": 0, "curr": 0}

    monkeypatch.setenv("CACHE_RETRIES", "1")
    monkeypatch.setenv("CACHE_DELAY", "0")
    monkeypatch.setattr(cm, "REQUIRED_FILES", missing)
    monkeypatch.setattr(cm, "missing_cache_files", lambda: missing)

    monkeypatch.setattr(
        cm, "_refresh_schema_concurrent", lambda: called.__setitem__("schema", 1)
    )

    async def fake_price(refresh=True):
        called["prices"] += 1
        missing.clear()
        return Path("cache/prices.json")

    monkeypatch.setattr(cm, "ensure_prices_cached_async", fake_price)
    monkeypatch.setattr(
        cm,
        "ensure_currencies_cached_async",
        lambda refresh=True: called.__setitem__("curr", 1),
    )

    ok, refreshed, schema_ref = await cm.fetch_missing_cache_files()
    assert ok is True and refreshed is True and schema_ref is False
    assert called["prices"] == 1
    assert called["schema"] == 0


@pytest.mark.asyncio
async def test_mixed_refresh(monkeypatch):
    missing = [Path("cache/schema/items.json"), Path("cache/prices.json")]
    called = {"schema": 0, "prices": 0}

    monkeypatch.setattr(cm, "REQUIRED_FILES", missing)
    monkeypatch.setattr(cm, "missing_cache_files", lambda: missing)
    monkeypatch.setenv("CACHE_RETRIES", "1")
    monkeypatch.setenv("CACHE_DELAY", "0")

    async def fake_schema():
        called["schema"] += 1
        missing.remove(Path("cache/schema/items.json"))

    async def fake_price(refresh=True):
        called["prices"] += 1
        missing.remove(Path("cache/prices.json"))
        return Path("cache/prices.json")

    monkeypatch.setattr(cm, "_refresh_schema_concurrent", fake_schema)
    monkeypatch.setattr(cm, "ensure_prices_cached_async", fake_price)
    monkeypatch.setattr(cm, "ensure_currencies_cached_async", lambda refresh=True: None)

    ok, refreshed, schema_ref = await cm.fetch_missing_cache_files()
    assert ok is True and refreshed is True and schema_ref is True
    assert called == {"schema": 1, "prices": 1}


@pytest.mark.asyncio
async def test_fetch_missing_failure(monkeypatch, capsys):
    missing = [Path("cache/schema/items.json")]
    calls = {"schema": 0}

    monkeypatch.setenv("CACHE_RETRIES", "3")
    monkeypatch.setenv("CACHE_DELAY", "0")
    monkeypatch.setattr(cm, "REQUIRED_FILES", missing)

    monkeypatch.setattr(cm, "missing_cache_files", lambda: missing)

    async def fake_schema():
        calls["schema"] += 1
        # do not clear missing so retries continue

    monkeypatch.setattr(cm, "_refresh_schema_concurrent", fake_schema)
    monkeypatch.setattr(cm, "ensure_prices_cached_async", lambda refresh=True: None)
    monkeypatch.setattr(cm, "ensure_currencies_cached_async", lambda refresh=True: None)

    ok, refreshed, schema_ref = await cm.fetch_missing_cache_files()
    out = capsys.readouterr().out
    assert "Failed after 3 retries" in out
    assert ok is False and refreshed is True and schema_ref is True
    assert calls["schema"] == 3


@pytest.mark.asyncio
async def test_skip_cache(monkeypatch, capsys):
    monkeypatch.setenv("SKIP_CACHE_INIT", "1")
    ok, refreshed, schema_ref = await cm.fetch_missing_cache_files()
    out = capsys.readouterr().out
    assert "\u26a0" in out
    assert ok is True
    assert refreshed is False
    assert schema_ref is False


@pytest.mark.asyncio
async def test_retry_note(monkeypatch, capsys):
    monkeypatch.setenv("CACHE_RETRIES", "4")
    monkeypatch.setenv("CACHE_DELAY", "1")

    monkeypatch.setattr(cm, "missing_cache_files", lambda: [])

    ok, refreshed, schema_ref = await cm.fetch_missing_cache_files()
    out = capsys.readouterr().out
    assert "Retrying up to 4 times with 1 sec delay" in out
    assert ok is True
    assert refreshed is False
    assert schema_ref is False


def test_incomplete_file_marked_missing(tmp_path, monkeypatch):
    file = tmp_path / "items.json"
    file.write_text("{}")
    monkeypatch.setattr(cm, "REQUIRED_FILES", [file])
    missing = cm.missing_cache_files()
    assert missing == [file]


def test_small_qualities_not_flagged(tmp_path, monkeypatch):
    qual = tmp_path / "qualities.json"
    qual.write_bytes(b"x" * 200)
    monkeypatch.setattr(cm, "REQUIRED_FILES", [qual])
    missing = cm.missing_cache_files()
    assert missing == []


def test_small_items_flagged(tmp_path, monkeypatch):
    item = tmp_path / "items.json"
    item.write_bytes(b"x" * 200)
    monkeypatch.setattr(cm, "REQUIRED_FILES", [item])
    missing = cm.missing_cache_files()
    assert missing == [item]


@pytest.mark.asyncio
async def test_incomplete_file_refetched(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cm, "MIN_SCHEMA_FILE_SIZE", 10)

    class FakeProvider(cm.SchemaProvider):
        def __init__(self, *a, **k):
            self.ENDPOINTS = {"items": "items"}
            self.cache_dir = tmp_path

        def _cache_file(self, key: str) -> Path:
            return self.cache_dir / f"{key}.json"

    monkeypatch.setattr(cm, "SchemaProvider", FakeProvider)

    async def fake_refresh():
        path = FakeProvider()._cache_file("items")
        await cm._save_json_atomic(path, "x" * 20)

    monkeypatch.setattr(cm, "_refresh_schema_concurrent", fake_refresh)
    monkeypatch.setattr(cm, "ensure_prices_cached_async", lambda refresh=True: None)
    monkeypatch.setattr(cm, "ensure_currencies_cached_async", lambda refresh=True: None)

    incomplete = tmp_path / "items.json"
    incomplete.write_text("{}")
    monkeypatch.setattr(cm, "REQUIRED_FILES", [incomplete])

    ok, refreshed, schema_ref = await cm.fetch_missing_cache_files()
    capsys.readouterr()
    assert ok is True
    assert refreshed is True
    assert schema_ref is True
    assert incomplete.stat().st_size > 10


def test_incomplete_pricing_marked_missing(tmp_path, monkeypatch):
    price = tmp_path / "prices.json"
    price.write_bytes(b"x" * 2048)
    curr = tmp_path / "currencies.json"
    curr.write_bytes(b"x" * 512)
    monkeypatch.setattr(cm, "REQUIRED_FILES", [price, curr])
    missing = cm.missing_cache_files()
    assert missing == [price, curr]


@pytest.mark.asyncio
async def test_incomplete_pricing_refetched(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cm, "MIN_PRICES_FILE_SIZE", 10)
    monkeypatch.setattr(cm, "MIN_CURRENCIES_FILE_SIZE", 10)

    async def fake_price(refresh=True):
        print("\u26a0 Detected incomplete price cache (5 bytes). Re-fetching...")
        (tmp_path / "prices.json").write_text("x" * 20)
        return Path(tmp_path / "prices.json")

    async def fake_curr(refresh=True):
        print("\u26a0 Detected incomplete currency cache (5 bytes). Re-fetching...")
        (tmp_path / "currencies.json").write_text("x" * 20)
        return Path(tmp_path / "currencies.json")

    price = tmp_path / "prices.json"
    price.write_text("{}")
    curr = tmp_path / "currencies.json"
    curr.write_text("{}")
    monkeypatch.setattr(cm, "REQUIRED_FILES", [price, curr])
    monkeypatch.setattr(cm, "_refresh_schema_concurrent", lambda: None)
    monkeypatch.setattr(cm, "ensure_prices_cached_async", fake_price)
    monkeypatch.setattr(cm, "ensure_currencies_cached_async", fake_curr)

    ok, refreshed, schema_ref = await cm.fetch_missing_cache_files()
    out = capsys.readouterr().out
    assert "Detected incomplete price cache" in out
    assert "currency cache" in out
    assert ok is True
    assert refreshed is True
    assert schema_ref is False
