import os
import types
import psutil
import importlib
from pathlib import Path


def test_kill_process_terminates_listening_process(monkeypatch):
    monkeypatch.setenv("SKIP_CACHE_INIT", "1")
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BPTF_API_KEY", "x")
    monkeypatch.setattr("utils.local_data.load_files", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(
        "utils.price_loader.ensure_prices_cached",
        lambda refresh=False: Path("prices.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached",
        lambda refresh=False: Path("currencies.json"),
    )
    called = {"terminated": False, "waited": False, "killed": False}

    class DummyLaddr:
        def __init__(self, port):
            self.port = port

    class DummyConn:
        def __init__(self, pid, port):
            self.status = psutil.CONN_LISTEN
            self.laddr = DummyLaddr(port)
            self.pid = pid

    conn = DummyConn(pid=9999, port=1234)

    monkeypatch.setattr(psutil, "net_connections", lambda kind="tcp": [conn])
    monkeypatch.setattr(os, "getpid", lambda: 1111)

    def fake_process(pid):
        assert pid == 9999
        proc = types.SimpleNamespace(
            terminate=lambda: called.__setitem__("terminated", True),
            wait=lambda timeout=5: called.__setitem__("waited", True),
            kill=lambda: called.__setitem__("killed", True),
        )
        return proc

    monkeypatch.setattr(psutil, "Process", fake_process)

    mod = importlib.import_module("app")
    mod.kill_process_on_port(1234)

    assert called["terminated"] is True
    assert called["waited"] is True
