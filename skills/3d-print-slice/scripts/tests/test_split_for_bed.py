from __future__ import annotations

import json
import struct
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
SPLIT = SCRIPTS / "split_for_bed.py"
VALIDATE_STL = (
    Path(__file__).resolve().parents[3] / "3d-print-validate" / "scripts" / "validate_stl.py"
)
TEMPLATE = (
    Path(__file__).resolve().parents[3] / "3d-print-openscad" / "templates" / "split_for_bed.scad"
)


def stl_bbox(path: Path):
    data = path.read_bytes()
    n = struct.unpack_from("<I", data, 80)[0]
    xs, ys, zs = [], [], []
    off = 84
    for _ in range(n):
        vals = struct.unpack_from("<12fH", data, off)
        off += 50
        for x, y, z in (vals[3:6], vals[6:9], vals[9:12]):
            xs.append(x)
            ys.append(y)
            zs.append(z)
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def run_split(out: Path, length=300.0, envelope=(256.0, 256.0, 256.0), clearance=0.2):
    return subprocess.run(
        [
            sys.executable,
            str(SPLIT),
            "--length-mm",
            str(length),
            "--envelope-mm",
            str(envelope[0]),
            str(envelope[1]),
            str(envelope[2]),
            "--clearance-per-side-mm",
            str(clearance),
            "--out",
            str(out),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def audit_body(stl: Path):
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATE_STL),
            "--stl",
            str(stl),
            "--build-x-mm",
            "256",
            "--build-y-mm",
            "256",
            "--build-z-mm",
            "256",
            "--expected-components",
            "1",
            "--min-wall-mm",
            "1.6",
            "--min-feature-mm",
            "1.6",
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def test_300mm_bar_splits_into_two_bodies_inside_256(tmp_path):
    out = tmp_path / "split"
    result = run_split(out)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((out / "split.json").read_text(encoding="utf-8"))
    assert report["scaled"] is False
    assert report["source_length_mm"] == 300.0
    assert report["clearance_per_side_mm"] == 0.2
    assert len(report["bodies"]) == 2
    a = out / "bar-a.stl"
    b = out / "bar-b.stl"
    assert a.is_file() and b.is_file()
    ba, bb = stl_bbox(a), stl_bbox(b)
    for box in (ba, bb):
        assert box[0] < 256 and box[1] < 256 and box[2] < 256, box
    assert ba[0] + bb[0] > 256, (ba, bb)
    assert abs((ba[0] + bb[0]) - 300.0) < 20.0 or ba[0] + bb[0] >= 290.0
    scad = (out / "bar-split.scad").read_text(encoding="utf-8")
    assert "clearance_per_side_mm = 0.2" in scad
    assert TEMPLATE.is_file()
    text = TEMPLATE.read_text(encoding="utf-8")
    assert "clearance_per_side_mm" in text
    assert "pin" in text.lower() or "key" in text.lower()
    for stl, label in ((a, "bar-a"), (b, "bar-b")):
        audited = audit_body(stl)
        assert audited.returncode == 0, f"{label}\n{audited.stdout}\n{audited.stderr}"
        assert "RESULT: PASS" in audited.stdout
        assert "components=1" in audited.stdout
        assert "HARD=0" in audited.stdout


def test_does_not_scale_a_half_that_still_overflows(tmp_path):
    result = run_split(tmp_path / "split", length=600.0, envelope=(200.0, 256.0, 256.0))
    assert result.returncode != 0
    assert "does not scale" in result.stderr or "does not scale" in result.stdout
