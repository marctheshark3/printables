"""scad_from_poly is pure Python. No Pillow, no OpenSCAD."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "scad_from_poly.py"
sys.path.insert(0, str(ROOT / "scripts"))

from scad_from_poly import clean_pts  # noqa: E402


def test_clean_pts_drops_closing_duplicate():
    pts = [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 0, "y": 0}]
    assert clean_pts(pts) == [{"x": 0, "y": 0}, {"x": 1, "y": 0}]


def test_clean_pts_keeps_open_ring():
    pts = [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 1, "y": 1}]
    assert clean_pts(pts) == pts


def test_cli_writes_named_plate(tmp_path):
    poly = tmp_path / "poly.json"
    poly.write_text(
        json.dumps(
            {
                "plate_mm": 80,
                "frame_mm": 8,
                "thickness_hint_mm": 2.4,
                "hole_policy": "filled",
                "source": "unit",
                "polygon": [
                    {"x": -10, "y": -10},
                    {"x": 10, "y": -10},
                    {"x": 0, "y": 12},
                    {"x": -10, "y": -10},
                ],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out" / "stencil.scad"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--poly", str(poly), "--out", str(out), "--name", "unit-stencil"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    assert "plate = 80" in text
    assert "thickness = 2.4" in text
    assert "[-10.0000, -10.0000]" in text
    assert text.count("[-10.0000, -10.0000]") == 1
    assert "name=unit-stencil" in text
