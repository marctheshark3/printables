#!/usr/bin/env python3
"""Extra extra: spawn pinned CadQuery Docker when PREVERSE_STEP_IMAGE is set.

Default CI does not run VibeCAD, CadQuery, Docker, AppImage, GPU, or qemu.
Never use cadquery/cadquery:latest (CQ 2.1 / Py 3.8).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src" / "bracket.py"


def main() -> int:
    image = os.environ.get("PREVERSE_STEP_IMAGE")
    if not image:
        print("SKIP: PREVERSE_STEP_IMAGE unset (default CI does not run CadQuery/OCC)")
        return 0
    if image.strip().endswith(":latest") or ":latest@" in image or ":latest/" in image:
        print("SKIP: PREVERSE_STEP_IMAGE must be a digest pin, not :latest")
        return 0
    if not SRC.is_file():
        print(f"HARD: missing {SRC}")
        return 2
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{PROJECT.resolve()}:/work",
        "-w",
        "/work",
        image,
        "python",
        "/work/src/bracket.py",
    ]
    print("+", " ".join(cmd))
    result = subprocess.run(cmd, check=False)
    return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
