import os
import types
import psutil
import importlib


def test_kill_process_terminates_listening_process(monkeypatch):
    called = {"terminated": False}

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
            terminate=lambda: called.__setitem__("terminated", True)
        )
        return proc

    monkeypatch.setattr(psutil, "Process", fake_process)

    mod = importlib.import_module("app")
    mod.kill_process_on_port(1234)

    assert called["terminated"] is True
