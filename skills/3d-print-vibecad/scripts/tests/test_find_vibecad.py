#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import stat
import sys
import urllib.error
from pathlib import Path
from unittest import mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import find_vibecad as fv  # noqa: E402


def test_supported_arch():
    assert fv.supported_arch("x86_64")
    assert fv.supported_arch("amd64")
    assert not fv.supported_arch("aarch64")
    assert not fv.supported_arch("arm64")


def test_find_cmd_env(tmp_path, monkeypatch):
    binary = tmp_path / "VibeCADCmd"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("VIBECAD_CMD", str(binary))
    assert fv.find_cmd() == binary


def test_status_missing_cmd_exit_1(monkeypatch, capsys):
    monkeypatch.setattr(fv, "supported_arch", lambda arch=None: True)
    monkeypatch.setattr(fv, "find_cmd", lambda explicit=None: None)
    rc = fv.main(["status"])
    assert rc == 1
    data = json.loads(capsys.readouterr().out)
    assert data["VIBECAD_CMD"] is None
    assert data["mcp"] == "do-not-enable"
    assert "releases" in data


def test_status_arm_exit_2(monkeypatch, capsys):
    monkeypatch.setattr(fv, "supported_arch", lambda arch=None: False)
    monkeypatch.setattr(fv, "machine", lambda: "aarch64")
    rc = fv.main(["status"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "ARM" in err


def test_asset_url_skips_arm():
    body = {
        "assets": [
            {"name": "VibeCAD-arm64.AppImage", "browser_download_url": "http://example/arm"},
            {"name": "VibeCAD-x86_64.AppImage", "browser_download_url": "http://example/amd"},
        ]
    }
    assert fv._asset_url(body) == "http://example/amd"


def test_download_refuses_arm(monkeypatch):
    monkeypatch.setattr(fv, "supported_arch", lambda arch=None: False)
    assert fv.main(["download"]) == 2


def test_fetch_falls_back_when_latest_is_prerelease_only():
    latest_req = None
    list_req = None

    class _Resp:
        def __init__(self, payload):
            self._payload = json.dumps(payload).encode("utf-8")

        def read(self):
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def opener(req, timeout=30):
        nonlocal latest_req, list_req
        url = req.full_url
        if url.endswith("/releases/latest"):
            latest_req = url
            raise urllib.error.HTTPError(url, 404, "Not Found", hdrs=None, fp=None)
        if url.endswith("/releases"):
            list_req = url
            return _Resp(
                [
                    {
                        "assets": [
                            {
                                "name": "VibeCAD-26.3.1-RC5-build7-Linux-x86_64.AppImage",
                                "browser_download_url": "http://example/rc5",
                            }
                        ]
                    }
                ]
            )
        raise AssertionError(url)

    import urllib.error

    assert fv.fetch_latest_appimage_url(opener=opener) == "http://example/rc5"
    assert latest_req.endswith("/releases/latest")
    assert list_req.endswith("/releases")


def test_http_status_no_listener():
    result = fv.http_status("http://127.0.0.1:9/v1/status", timeout=0.05)
    assert result["listening"] is False
    assert result["ok"] is False
