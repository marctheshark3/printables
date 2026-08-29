#!/usr/bin/env python3
"""Secret scan shared with CI: synthetic needles match; the tree stays clean."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Keep in lockstep with the grep in .github/workflows/ci.yml.
# Python `re` does not implement POSIX `[:space:]`; CI grep does.
PY_SECRET_PATTERN = re.compile(
    r"BAMBU_ACCESS_CODE="
    r"|spark-adb4"
    r"|tailf9bab6"
    r"|\.ts\.net"
    r"|/home/[A-Za-z0-9._-]+"
    r"|~/Documents/the-grid"
    r"|BEGIN (RSA|OPENSSH) PRIVATE"
    r"|[\t ]gho_[A-Za-z0-9]+"
    r"|[\t ]ghp_[A-Za-z0-9]+"
    r"|access_code.{0,48}(?:[0-9]{1,3}\.){3}[0-9]{1,3}"
    r"|(?:[0-9]{1,3}\.){3}[0-9]{1,3}.{0,48}access_code",
    re.I | re.M,
)

# Same roots as the CI grep, plus public prose. Goal docs may quote needles.
SCAN_ROOTS = (
    ROOT / "skills",
    ROOT / "examples",
    ROOT / "install.sh",
    ROOT / "README.md",
    ROOT / "STATUS.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "SECURITY.md",
    ROOT / "skill-bundles",
    ROOT / ".env.example",
)

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules"}

SYNTHETIC = [
    "BAMBU_ACCESS_CODE=secret",
    "access_code: 192.168.1.50",
    "192.168.0.10 access_code",
    "spark-adb4",
    "tailf9bab6",
    "host.example.ts.net",
    "/home/whaleshark/secret",
    "~/Documents/the-grid",
    "BEGIN RSA PRIVATE",
    " gho_abcdefghijklmnop",
    " ghp_abcdefghijklmnop",
]


def iter_scan_files():
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        if root.is_file():
            yield root
            continue
        for path in root.rglob("*"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.is_file():
                yield path


def test_synthetic_needles_match():
    for needle in SYNTHETIC:
        assert PY_SECRET_PATTERN.search(needle), needle


def test_repo_tree_is_clean():
    hits = []
    for path in iter_scan_files():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if PY_SECRET_PATTERN.search(text):
            hits.append(str(path.relative_to(ROOT)))
    assert hits == [], f"secret-like values in {hits}"
