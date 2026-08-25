#!/usr/bin/env python3
"""Synthetic cube STL + DESIGN.md — dfm_gate must PASS (no Docker)."""
from __future__ import annotations

import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GATE = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "openscad-printables"
    / "scripts"
    / "dfm_gate.py"
)


def write_cube_stl(path: Path, size: float = 20.0) -> None:
    """Axis-aligned cube [0,size]^3 as binary STL (12 tris)."""
    s = float(size)
    # 6 faces, 2 tris each. Vertices of the cube.
    v = [
        (0.0, 0.0, 0.0),
        (s, 0.0, 0.0),
        (s, s, 0.0),
        (0.0, s, 0.0),
        (0.0, 0.0, s),
        (s, 0.0, s),
        (s, s, s),
        (0.0, s, s),
    ]
    faces = [
        (0, 2, 1),
        (0, 3, 2),  # z=0
        (4, 5, 6),
        (4, 6, 7),  # z=s
        (0, 1, 5),
        (0, 5, 4),  # y=0
        (3, 7, 6),
        (3, 6, 2),  # y=s
        (0, 4, 7),
        (0, 7, 3),  # x=0
        (1, 2, 6),
        (1, 6, 5),  # x=s
    ]
    buf = bytearray(80)  # header
    buf += struct.pack("<I", len(faces))
    for i0, i1, i2 in faces:
        a, b, c = v[i0], v[i1], v[i2]
        # outward-ish normal unused by most of the gate
        buf += struct.pack("<3f", 0.0, 0.0, 0.0)
        buf += struct.pack("<3f", *a)
        buf += struct.pack("<3f", *b)
        buf += struct.pack("<3f", *c)
        buf += struct.pack("<H", 0)
    path.write_bytes(buf)


DESIGN = """---
product_class: bracket
print_orientation: feet-down
print_up_axis: Z
use_flip: no
soft_mode: no
stack_story: none
clearance_mm: 0.8
expected_components: 1
fit_required: no
critical_fit_status: none
service_environment: dry
drainage: none
---

# Coupon bracket

Synthetic 20 mm cube for CI. Not a household part.
"""


class TestDfmGateCube(unittest.TestCase):
    def test_gate_script_exists(self):
        self.assertTrue(GATE.is_file(), GATE)

    def test_cube_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "docs").mkdir()
            (root / "stl").mkdir()
            (root / "docs" / "DESIGN.md").write_text(DESIGN, encoding="utf-8")
            stl = root / "stl" / "cube.stl"
            write_cube_stl(stl)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(GATE),
                    "--project",
                    str(root),
                    "--stl",
                    str(stl),
                    "--mode-file",
                    str(root / "docs" / "DESIGN.md"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                self.fail(
                    f"dfm_gate exit {proc.returncode}\n"
                    f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
                )
            self.assertIn("RESULT: PASS", proc.stdout)

    def test_missing_mode_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "stl").mkdir()
            stl = root / "stl" / "cube.stl"
            write_cube_stl(stl)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(GATE),
                    "--project",
                    str(root),
                    "--stl",
                    str(stl),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            # Missing product_class / orientation is a HARD fail (G-mode).
            self.assertNotEqual(proc.returncode, 0, proc.stdout)
            self.assertIn("HARD", proc.stdout)


class TestModeParse(unittest.TestCase):
    def test_frontmatter_keys(self):
        sys.path.insert(0, str(GATE.parent))
        import dfm_gate  # type: ignore

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "DESIGN.md"
            p.write_text(DESIGN, encoding="utf-8")
            mode = dfm_gate.read_mode_file(p)
        self.assertEqual(mode.get("product_class"), "bracket")
        self.assertEqual(mode.get("print_orientation"), "feet-down")
        self.assertEqual(mode.get("print_up_axis"), "Z")


if __name__ == "__main__":
    unittest.main()
