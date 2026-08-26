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
            self.assertTrue((root / "docs" / "PRINT_SPEC.yaml").is_file())
            text = (root / "docs" / "DESIGN.md").read_text(encoding="utf-8")
            self.assertIn("PRINT_SPEC.yaml", text)
            self.assertIn("enclosure", text)
            self.assertNotIn("expected_components:", text)
            spec = (root / "docs" / "PRINT_SPEC.yaml").read_text(encoding="utf-8")
            self.assertIn("backend: blender", spec)
            self.assertIn("parametric: true", spec)
            self.assertIn("parameter: OUTER_X", spec)
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


class TestFindValidator(unittest.TestCase):
    def test_print_validator_env(self):
        with tempfile.NamedTemporaryFile() as handle:
            with mock.patch.dict(os.environ, {"PRINT_VALIDATOR": handle.name}, clear=False):
                self.assertEqual(pb.find_project_validator(), Path(handle.name))

    def test_dfm_gate_alias(self):
        with tempfile.NamedTemporaryFile() as handle:
            with mock.patch.dict(os.environ, {"DFM_GATE": handle.name}, clear=False):
                os.environ.pop("PRINT_VALIDATOR", None)
                self.assertEqual(pb.find_project_validator(), Path(handle.name))

    def test_profile_glob_without_hardcoded_tron(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            candidate = (
                home / ".hermes/profiles/alice/skills/creative/"
                "3d-print-validate/scripts/validate_project.py"
            )
            candidate.parent.mkdir(parents=True)
            candidate.write_text("# validator\n", encoding="utf-8")
            with mock.patch.object(pb, "SKILL_ROOT", home / "missing-skill"):
                with mock.patch.object(Path, "home", return_value=home):
                    with mock.patch.dict(os.environ, {}, clear=False):
                        os.environ.pop("PRINT_VALIDATOR", None)
                        os.environ.pop("DFM_GATE", None)
                        self.assertEqual(pb.find_project_validator(), candidate)


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
