#!/usr/bin/env python3
"""Bind CAD inspector onto Tailscale IPv4 only. Does not listen on 0.0.0.0."""
from __future__ import annotations

import argparse
import select
import socket
import subprocess
import threading


def tailscale_ipv4() -> str:
    try:
        out = subprocess.check_output(["tailscale", "ip", "-4"], text=True, timeout=5).strip()
        ip = out.splitlines()[0].strip()
        if ip.startswith("100."):
            return ip
    except (OSError, subprocess.CalledProcessError, IndexError):
        pass
    raise SystemExit("HARD: tailscale ip -4 did not return a 100.x address")


def pipe(a: socket.socket, b: socket.socket) -> None:
    try:
        while True:
            r, _, _ = select.select([a, b], [], [], 60)
            if not r:
                continue
            for src in r:
                dst = b if src is a else a
                data = src.recv(65536)
                if not data:
                    return
                dst.sendall(data)
    except OSError:
        return
    finally:
        for s in (a, b):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            s.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8107)
    parser.add_argument("--listen", default=None, help="Tailscale IPv4 (default: tailscale ip -4)")
    parser.add_argument("--upstream-host", default="127.0.0.1")
    args = parser.parse_args(argv)
    listen_ip = args.listen or tailscale_ipv4()
    if listen_ip in {"0.0.0.0", "::", "*"} or listen_ip.startswith("192.168."):
        raise SystemExit("HARD: Tailscale IPv4 only — not 0.0.0.0 / LAN")
    listen = (listen_ip, args.port)
    upstream = (args.upstream_host, args.port)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(listen)
    srv.listen(64)
    print(f"CAD inspector Tailscale proxy {listen[0]}:{listen[1]} -> {upstream[0]}:{upstream[1]}", flush=True)
    while True:
        client, _addr = srv.accept()
        up = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            up.connect(upstream)
        except OSError:
            client.close()
            continue
        threading.Thread(target=pipe, args=(client, up), daemon=True).start()


if __name__ == "__main__":
    raise SystemExit(main())
