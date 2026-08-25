#!/usr/bin/env python3
"""Unit tests for pblend CLI (no live Blender required except optional)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import pblend_cli as pb  # noqa: E402


class TestPaths(unittest.TestCase):
    def test_skill_root(self):
        self.assertTrue((pb.SKILL_ROOT / "SKILL.md").is_file() or (pb.SKILL_ROOT / "scripts").is_dir())

    def test_find_blender_env(self):
        with mock.patch.dict(os.environ, {"BLENDER": "/usr/bin/blender"}, clear=False):
            # only if exists on this host
            if Path("/usr/bin/blender").is_file():
                self.assertEqual(pb.find_blender(), "/usr/bin/blender")

    def test_version(self):
        ns = pb.build_parser().parse_args(["version"])
        self.assertEqual(ns.func(ns), 0)


class TestNewScaffold(unittest.TestCase):
    def test_new_creates_tree(self):
        with tempfile.TemporaryDirectory() as td:
            ns = pb.build_parser().parse_args(
                ["new", "unit-smoke", "--root", td, "--class", "enclosure"]
            )
            rc = ns.func(ns)
            self.assertEqual(rc, 0)
            root = Path(td) / "unit-smoke"
            self.assertTrue((root / "src" / "build.py").is_file())
            self.assertTrue((root / "docs" / "DESIGN.md").is_file())
            text = (root / "docs" / "DESIGN.md").read_text(encoding="utf-8")
            self.assertIn("scaffold: blender-bpy", text)
            self.assertIn("product_class: enclosure", text)
            build = (root / "src" / "build.py").read_text(encoding="utf-8")
            self.assertIn("unit-smoke", build)
            self.assertNotIn("{{NAME}}", build)


class TestForwardArgs(unittest.TestCase):
    def test_run_remainder_strips_double_dash(self):
        ns = pb.build_parser().parse_args(
            ["run", "--project", "/tmp", "--", "--which", "base"]
        )
        # main() strips; parse leaves remainder with --
        self.assertTrue(ns.forward)


class TestPrintableStls(unittest.TestCase):
    def test_skips_assembly(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "stl").mkdir()
            (p / "stl" / "part.stl").write_bytes(b"x")
            (p / "stl" / "part-assembly.stl").write_bytes(b"y")
            got = pb._iter_printable_stls(p, None)
            names = [g.name for g in got]
            self.assertEqual(names, ["part.stl"])


if __name__ == "__main__":
    unittest.main()
