#!/usr/bin/env python3
"""Detect (and optionally fetch) the 10-X-eng/vibecad AppImage / Cmd binary.

Does not vendor VibeCAD. Does not enable MCP. Does not print tokens.
Linux ARM qemu-x86_64 AppImage is not a supported backend.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import stat
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable, List, Optional

RELEASES = "https://github.com/10-X-eng/vibecad/releases/latest"
RELEASES_API = "https://api.github.com/repos/10-X-eng/vibecad/releases/latest"
RELEASES_LIST_API = "https://api.github.com/repos/10-X-eng/vibecad/releases"
AGENT_TOKEN = Path.home() / ".local" / "share" / "VibeCAD" / "agent" / "token"
DEFAULT_HTTP = "http://127.0.0.1:8766/v1/status"
INSTALL_DIR = Path.home() / ".local" / "opt" / "vibecad"


def machine() -> str:
    return (platform.machine() or "").lower()


def supported_arch(arch: Optional[str] = None) -> bool:
    arch = (arch or machine()).lower()
    return arch in {"x86_64", "amd64"}


def is_executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def looks_like_cmd(path: Path) -> bool:
    name = path.name.lower()
    return (
        "vibecadcmd" in name
        or name == "freecadcmd"
        or name.endswith(".appimage")
        or "vibecad" in name and "appimage" in name
    )


def candidate_paths(explicit: Optional[str] = None) -> List[Path]:
    found: List[Path] = []
    if explicit:
        found.append(Path(explicit).expanduser())
    env = os.environ.get("VIBECAD_CMD")
    if env:
        found.append(Path(env).expanduser())
    for name in ("VibeCADCmd", "vibecadcmd", "freecadcmd", "VibeCAD"):
        which = shutil.which(name)
        if which:
            found.append(Path(which))
    home = Path.home()
    globs = [
        home / ".local" / "opt" / "vibecad" / "*",
        home / ".local" / "bin" / "VibeCADCmd",
        home / ".local" / "bin" / "freecadcmd",
        home / "Applications" / "VibeCAD*.AppImage",
        Path("/usr/bin/freecadcmd"),
        Path("/opt/vibecad/bin/VibeCADCmd"),
        Path("/opt/vibecad/bin/freecadcmd"),
    ]
    for pattern in globs:
        if "*" in str(pattern):
            found.extend(sorted(pattern.parent.glob(pattern.name)))
        else:
            found.append(pattern)
    seen = set()
    out: List[Path] = []
    for path in found:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def find_cmd(explicit: Optional[str] = None) -> Optional[Path]:
    forced = set()
    if explicit:
        forced.add(str(Path(explicit).expanduser()))
    env = os.environ.get("VIBECAD_CMD")
    if env:
        forced.add(str(Path(env).expanduser()))
    forced_hits: List[Path] = []
    cmd_hits: List[Path] = []
    other: List[Path] = []
    for path in candidate_paths(explicit):
        if not is_executable(path):
            continue
        if str(path) in forced:
            forced_hits.append(path)
            continue
        if not looks_like_cmd(path):
            continue
        if "cmd" in path.name.lower():
            cmd_hits.append(path)
        else:
            other.append(path)
    for group in (forced_hits, cmd_hits, other):
        if group:
            return group[0]
    return None


def http_status(url: str = DEFAULT_HTTP, timeout: float = 0.4) -> dict:
    token_path = AGENT_TOKEN
    headers = {}
    if token_path.is_file():
        token = token_path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"ok": True, "http": int(getattr(resp, "status", 200)), "listening": True}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "http": int(exc.code), "listening": True}
    except Exception:
        return {"ok": False, "http": None, "listening": False}


def status_payload(explicit: Optional[str] = None, *, probe_http: bool = False) -> dict:
    arch = machine()
    cmd = find_cmd(explicit)
    payload = {
        "supported_arch": supported_arch(arch),
        "arch": arch,
        "releases": RELEASES,
        "VIBECAD_CMD": str(cmd) if cmd else None,
        "token_file_present": AGENT_TOKEN.is_file(),
        "mcp": "do-not-enable",
        "http": None,
    }
    if probe_http:
        payload["http"] = http_status()
    return payload


def cmd_status(args: argparse.Namespace) -> int:
    if not supported_arch():
        print(
            "HARD: Linux ARM qemu-x86_64 AppImage is not a supported backend. "
            "Use an x86_64 host and the 10-X-eng/vibecad AppImage.",
            file=sys.stderr,
        )
        data = status_payload(args.cmd, probe_http=args.probe_http)
        print(json.dumps(data, sort_keys=True, indent=2))
        return 2
    data = status_payload(args.cmd, probe_http=args.probe_http)
    print(json.dumps(data, sort_keys=True, indent=2))
    if not data["VIBECAD_CMD"]:
        print(
            f"HINT: download the x86_64 AppImage from {RELEASES} then:\n"
            f"  chmod +x VibeCAD*.AppImage\n"
            f"  export VIBECAD_CMD=$PWD/VibeCAD*.AppImage",
            file=sys.stderr,
        )
        return 1
    print(f"export VIBECAD_CMD={data['VIBECAD_CMD']}", file=sys.stderr)
    return 0


def _asset_url(body: dict) -> Optional[str]:
    for asset in body.get("assets") or []:
        name = str(asset.get("name") or "").lower()
        url = asset.get("browser_download_url")
        if not url:
            continue
        if not name.endswith(".appimage"):
            continue
        if any(tag in name for tag in ("aarch64", "arm64", "armhf")):
            continue
        if "x86_64" in name or "amd64" in name or "x64" in name or "linux" in name:
            return str(url)
    return None


def _github_json(url: str, opener=None):
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "printables-find-vibecad"},
    )
    open_url = opener or urllib.request.urlopen
    with open_url(req, timeout=30) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8"))


def fetch_latest_appimage_url(opener=None) -> str:
    """Resolve an x86_64 AppImage. /releases/latest 404s when only prereleases exist."""
    try:
        body = _github_json(RELEASES_API, opener)
        url = _asset_url(body)
        if url:
            return url
    except urllib.error.HTTPError as exc:
        if int(exc.code) != 404:
            raise
    listing = _github_json(RELEASES_LIST_API, opener)
    if isinstance(listing, dict):
        listing = [listing]
    for body in listing or []:
        url = _asset_url(body)
        if url:
            return url
    raise RuntimeError("no x86_64 AppImage on 10-X-eng/vibecad releases")


def cmd_download(args: argparse.Namespace) -> int:
    if not supported_arch():
        print("HARD: refusing to download an AppImage on non-x86_64.", file=sys.stderr)
        return 2
    dest_dir = Path(args.dest).expanduser() if args.dest else INSTALL_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        url = fetch_latest_appimage_url()
    except Exception as exc:
        print(f"HARD: could not resolve latest AppImage: {exc}", file=sys.stderr)
        print(f"HINT: download manually from {RELEASES}", file=sys.stderr)
        return 2
    dest = dest_dir / "VibeCAD.AppImage"
    print(f"GET {url}", file=sys.stderr)
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as exc:
        print(f"HARD: download failed: {exc}", file=sys.stderr)
        return 2
    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    wrapper = dest_dir / "VibeCADCmd"
    wrapper.write_text(
        "#!/bin/sh\n"
        'APP="$(dirname "$(readlink -f "$0")")/VibeCAD.AppImage"\n'
        'export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"\n'
        'exec "$APP" freecadcmd "$@"\n',
        encoding="utf-8",
    )
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"export VIBECAD_CMD={wrapper}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Find 10-X-eng/vibecad Cmd / AppImage")
    p.add_argument("--cmd", help="explicit binary or AppImage")
    p.add_argument("--probe-http", action="store_true", help="GET 127.0.0.1:8766/v1/status; never print the token")
    sub = p.add_subparsers(dest="command")
    sub.add_parser("status", help="print JSON status (default)")
    dl = sub.add_parser("download", help="fetch latest x86_64 AppImage into ~/.local/opt/vibecad/")
    dl.add_argument("--dest", type=Path, default=None)
    return p


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.command == "download":
        return cmd_download(args)
    return cmd_status(args)


if __name__ == "__main__":
    raise SystemExit(main())
