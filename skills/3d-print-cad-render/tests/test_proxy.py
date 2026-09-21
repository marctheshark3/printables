from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ts_proxy_cad import is_tailscale_ipv4, require_tailscale_ipv4  # noqa: E402


def test_tailscale_range_rejects_lan():
    assert is_tailscale_ipv4("100.64.0.1")
    assert is_tailscale_ipv4("100.127.255.254")
    for bad in ("10.0.0.5", "172.16.0.5", "192.168.1.1", "0.0.0.0", "100.63.255.255", "100.128.0.1"):
        assert not is_tailscale_ipv4(bad)
        with pytest.raises(SystemExit, match="Tailscale"):
            require_tailscale_ipv4(bad)
