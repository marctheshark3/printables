#!/usr/bin/env python3
"""Emit a slicer process card from PRINT_SPEC; optional 3MF if a slicer CLI exists."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

BRIEF = Path(__file__).resolve().parent.parent.parent / "3d-print-design-brief" / "scripts"
sys.path.insert(0, str(BRIEF))

from print_spec import load_spec  # noqa: E402

SLICER_ENV = ("ORCA_SLICER", "BAMBU_STUDIO", "PRUSA_SLICER")


def find_slicer() -> Path | None:
    for name in SLICER_ENV:
        value = os.environ.get(name)
        if not value:
            continue
        path = Path(value).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return path
        resolved = shutil.which(value)
        if resolved:
            cand = Path(resolved)
            if cand.is_file() and os.access(cand, os.X_OK):
                return cand
    return None


def process_card(spec, body) -> dict:
    return {
        "body": body.body,
        "stl": body.path,
        "printer": spec.printer,
        "build_volume_mm": list(spec.build_volume_mm),
        "nozzle_mm": spec.nozzle_mm,
        "layer_height_mm": spec.layer_height_mm,
        "material": spec.material,
        "bed_face": spec.bed_face,
        "up_axis": spec.up_axis,
        "orientation": spec.orientation,
        "supports": spec.supports,
        "max_overhang_deg": spec.max_overhang_deg,
    }


def try_write_3mf(slicer: Path, stl: Path, out_3mf: Path) -> bool:
    """Invoke a slicer CLI. Never copy or rename the STL as a 3MF."""
    out_3mf.parent.mkdir(parents=True, exist_ok=True)
    attempts = (
        [str(slicer), "--export-3mf", "-o", str(out_3mf), str(stl)],
        [str(slicer), "--export-3mf", "--output", str(out_3mf), str(stl)],
        [str(slicer), "--slice", "--export-3mf", str(out_3mf), str(stl)],
    )
    stl_bytes = stl.read_bytes() if stl.is_file() else b""
    for argv in attempts:
        if out_3mf.exists():
            out_3mf.unlink()
        result = subprocess.run(argv, text=True, capture_output=True, check=False)
        if not out_3mf.is_file():
            continue
        data = out_3mf.read_bytes()
        if not data or data == stl_bytes:
            out_3mf.unlink()
            continue
        if result.returncode == 0:
            return True
        out_3mf.unlink()
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit process cards and optional 3MF")
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    spec, errors = load_spec(project / "docs" / "PRINT_SPEC.yaml", project=project)
    if spec is None or errors:
        for error in errors:
            print(f"HARD: {error}")
        return 1

    slicer = find_slicer()
    wrote_3mf = False
    for body in spec.stl_files:
        card = process_card(spec, body)
        out_json = project / "slice" / f"{body.body}.process.json"
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
        print(f"PROCESS_CARD: {out_json.relative_to(project)}")
        if slicer is None:
            continue
        out_3mf = project / "slice" / f"{body.body}.3mf"
        if try_write_3mf(slicer, project / body.path, out_3mf):
            print(f"THREE_MF: {out_3mf.relative_to(project)}")
            wrote_3mf = True
        else:
            print(f"SKIP: slicer CLI did not emit 3MF for {body.body}")

    if slicer is None:
        print("SKIP: no slicer CLI")
    elif not wrote_3mf:
        print("SKIP: no slicer CLI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
