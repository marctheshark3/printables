#!/usr/bin/env python3
"""Serve the CAD inspector on loopback. No directory listing. Never 0.0.0.0."""
from __future__ import annotations

import argparse
import re
import socket
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ALLOWED_SUFFIX = {".html", ".js", ".png", ".jpg", ".jpeg", ".md", ".css"}
JSON_ROOT = {"catalog.json", "study.json"}
MODEL_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def json_allowed(relative: Path) -> bool:
    if relative.suffix.lower() != ".json":
        return False
    if len(relative.parts) == 1 and relative.name in JSON_ROOT:
        return True
    return (
        len(relative.parts) == 2
        and relative.parts[0] == "models"
        and MODEL_ID.match(relative.stem) is not None
    )


class V6Server(ThreadingHTTPServer):
    address_family = socket.AF_INET6


class ViewerHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        path = unquote(urlsplit(self.path).path)
        if path == "/":
            path = "/viewer.html"
        relative = Path(path.lstrip("/"))
        root = Path(self.directory).resolve()
        candidate = (root / relative).resolve()
        if (
            ".." in relative.parts
            or not candidate.is_relative_to(root)
            or not candidate.is_file()
            or not (json_allowed(relative) or relative.suffix.lower() in ALLOWED_SUFFIX)
        ):
            self.send_error(404, "Viewer asset not found")
            return None
        self.path = path
        return super().send_head()

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def make_server(root: Path, port: int, bind: str = "127.0.0.1"):
    if bind not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("CAD inspector bind must be loopback (127.0.0.1), not %s" % bind)
    if port != 0 and not 1 <= port <= 65535:
        raise ValueError("port out of range")
    handler = partial(ViewerHandler, directory=str(root.resolve()))
    server_cls = V6Server if bind == "::1" else ThreadingHTTPServer
    return server_cls((bind, port), handler)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8107)
    parser.add_argument("--bind", default="127.0.0.1")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not (root / "viewer.html").is_file():
        parser.error(f"missing {root / 'viewer.html'}")
    try:
        server = make_server(root, args.port, args.bind)
    except ValueError as exc:
        parser.error(str(exc))
    print(f"CAD inspector: http://{args.bind}:{args.port}/?view=solid", flush=True)
    print("Loopback only. Ctrl-C stops.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
