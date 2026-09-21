from __future__ import annotations

import sys
import socket
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from serve_cad_viewer import make_server  # noqa: E402


def test_bind_rejects_all_interfaces():
    with pytest.raises(ValueError, match="loopback"):
        make_server(ROOT, 8097, "0.0.0.0")


def test_serves_viewer_and_hides_step(tmp_path):
    (tmp_path / "viewer.html").write_text("<html>ok</html>")
    (tmp_path / "secret.step").write_text("ISO-10303")
    server = make_server(tmp_path, 0, "127.0.0.1")
    port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/")
        res = conn.getresponse()
        body = res.read()
        assert res.status == 200
        assert b"ok" in body
        conn.request("GET", "/secret.step")
        assert conn.getresponse().status == 404
        (tmp_path / "part.scene.json").write_text('{"step_path":"/tmp/hidden.step"}')
        (tmp_path / "catalog.json").write_text("{}")
        (tmp_path / "models").mkdir()
        (tmp_path / "models" / "box.json").write_text("{}")
        conn.request("GET", "/part.scene.json")
        assert conn.getresponse().status == 404
        conn.request("GET", "/catalog.json")
        assert conn.getresponse().status == 200
        conn.request("GET", "/models/box.json")
        assert conn.getresponse().status == 200
        conn.request("GET", "/../viewer.template.html")
        # path traversal must 404
        assert conn.getresponse().status == 404
        conn.close()
    finally:
        server.shutdown()
        server.server_close()


def test_bind_ipv6_loopback(tmp_path):
    (tmp_path / "viewer.html").write_text("ok")
    try:
        server = make_server(tmp_path, 0, "::1")
    except OSError as exc:
        pytest.skip(f"no ipv6 loopback: {exc}")
    server.server_close()
    assert server.address_family == socket.AF_INET6
