"""Scale-gate tests. No OpenCV. No photos."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "charuco_photo.py"


def load():
    spec = importlib.util.spec_from_file_location("charuco_photo", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_nearest_gap_on_15mm_grid():
    mod = load()
    points = [(0.0, 0.0), (15.0, 0.0), (0.0, 15.0), (15.0, 15.0)]
    assert mod.median_nearest_gap(points) == 15.0


def test_square_tolerance_edges():
    mod = load()
    assert mod.square_within_tol(15.0)
    assert mod.square_within_tol(15.15)
    assert mod.square_within_tol(14.85)
    assert not mod.square_within_tol(15.151)
    assert not mod.square_within_tol(14.849)
    assert not mod.square_within_tol(None)


def test_photo_required_without_opencv():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", "unused"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "photo required" in result.stderr
