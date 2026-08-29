"""Committed microduck/lamp STL cases. Extra trees via PREVERSE_EXTRA_STL_ROOT."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from compare_deviation import compare_meshes
from extract_sketches import apply_sketches
from hypothesize_features import hypothesize_features
from mesh_analyze import analyze_stl
from rebuild_cad import emit_cadquery_source
from segment_surfaces import apply_segment, load_aligned_mesh
from tessellate_solid import tessellate_ir

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPTS = Path(__file__).resolve().parents[1]
PREVERSE = SCRIPTS / "preverse_cli.py"


def test_speaker_box_is_parametric_extrude(tmp_path: Path):
    src = FIXTURES / "speaker.stl"
    assert src.is_file()
    stl = tmp_path / "speaker.stl"
    stl.write_bytes(src.read_bytes())
    ir, code = analyze_stl(stl, body="speaker")
    assert code == 0
    assert ir["input_triangles"] == 12
    mesh = load_aligned_mesh(stl, ir)
    ir = hypothesize_features(apply_sketches(apply_segment(ir, mesh), mesh))
    assert ir["class"] == "parametric"
    types = [f["type"] for f in ir["features"]]
    assert types.count("extrude") == 1
    report = compare_meshes(stl, tessellate_ir(ir), ir)
    assert report["pass"] is True, report
    assert report["max"] <= ir["tolerance"]["max_deviation_mm"]
    cq = emit_cadquery_source(ir)
    # Sketch x_axis is world -Y, y_axis is world +X: UV is depth × width, not width × depth.
    assert "wp.rect(depth_mm, width_mm)" in cq
    assert "wp.rect(width_mm, depth_mm)" not in cq


def test_inverted_coupon_fixture_fails_analyze():
    stl = FIXTURES / "coupon_150x150x3.stl"
    assert stl.is_file()
    ir, code = analyze_stl(stl, body="coupon")
    assert code == 2
    assert ir["class"] == "failed"
    assert any("volume" in w for w in ir["warnings"])
    assert ir["topology"]["volume_mm3"] < 0


def test_light_cover_open_mesh_fails_and_export_refuses(tmp_path: Path):
    src = FIXTURES / "light-cover.stl"
    assert src.is_file()
    stl = tmp_path / "light-cover.stl"
    stl.write_bytes(src.read_bytes())
    ir, code = analyze_stl(stl, body="light_cover")
    assert code == 2
    assert ir["class"] == "failed"
    assert ir["topology"]["boundary_edges"] > 0
    env = os.environ.copy()
    env.pop("VIBECAD_CMD", None)
    env.pop("PREVERSE_STEP_IMAGE", None)
    env.pop("PREVERSE_PYTHON", None)
    result = subprocess.run(
        [
            sys.executable,
            str(PREVERSE),
            "run",
            "--stl",
            str(stl),
            "--project",
            str(tmp_path),
            "--body",
            "light_cover",
        ],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode != 0
    assert not (tmp_path / "step" / "light_cover.step").exists()
    assert not (tmp_path / "stl" / "light_cover.stl").exists()


def extra_stl_paths() -> list[Path]:
    root = os.environ.get("PREVERSE_EXTRA_STL_ROOT")
    if not root:
        return []
    path = Path(root)
    if not path.is_dir():
        return []
    return sorted(p for p in path.glob("*.stl") if p.is_file())


def test_extra_stls_never_invent_step(tmp_path: Path):
    paths = extra_stl_paths()
    if not paths:
        pytest.skip("set PREVERSE_EXTRA_STL_ROOT to a directory of extra STLs")
    env = os.environ.copy()
    env.pop("VIBECAD_CMD", None)
    env.pop("PREVERSE_STEP_IMAGE", None)
    env.pop("PREVERSE_PYTHON", None)
    for stl in paths:
        dest = tmp_path / stl.stem
        dest.mkdir()
        ir, code = analyze_stl(stl, body=stl.stem)
        if code == 2:
            assert ir["class"] == "failed", stl.name
            continue
        topo = ir.get("topology") or {}
        tris = int(ir.get("input_triangles") or 0)
        shells = int(topo.get("components") or 1)
        # Large or multi-shell scans are legal meshes but not v1 prismatic
        # coupons. Analyze already ran; do not spend CI reconstructing them.
        if tris > 500 or shells != 1:
            continue
        result = subprocess.run(
            [
                sys.executable,
                str(PREVERSE),
                "export",
                "--stl",
                str(stl),
                "--project",
                str(dest),
                "--body",
                stl.stem,
            ],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
        # Missing kernel → 2; class=failed after features → 1. Never write STEP.
        assert result.returncode != 0, f"{stl.name}: unexpected success\n{result.stderr}\n{result.stdout}"
        assert not (dest / "step").exists() or not any((dest / "step").glob("*.step")), stl.name
