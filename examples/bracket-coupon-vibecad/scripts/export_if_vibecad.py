#!/usr/bin/env python3
"""Extra extra: run the gold .py inside VibeCAD when VIBECAD_CMD is set.

Writes stl/bracket-coupon.stl and step/bracket-coupon.step via Mesh.export
and Part.export. Default CI does not run VibeCAD, Docker, AppImage, GPU, or qemu.
ARM qemu-x86_64 AppImage is unsupported.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
SRC = PROJECT / "src" / "bracket-coupon.py"
VALIDATOR = REPO / "skills" / "3d-print-validate" / "scripts" / "validate_project.py"


def main() -> int:
    cmd = os.environ.get("VIBECAD_CMD")
    if not cmd:
        print("SKIP: VIBECAD_CMD unset (default CI does not run VibeCAD)")
        return 0
    exported = subprocess.run([cmd, str(SRC)], cwd=str(PROJECT), check=False)
    if exported.returncode:
        print(f"HARD: VIBECAD_CMD export failed exit={exported.returncode}")
        return exported.returncode
    gated = subprocess.run(
        [sys.executable, str(VALIDATOR), str(PROJECT)], check=False
    )
    return gated.returncode


if __name__ == "__main__":
    raise SystemExit(main())
