from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from export_step import refuse_triangle_wrap, write_ir_stl
from mesh_analyze import analyze_stl
from mesh_fixtures import cube_tris, triangle_soup_step
from stl_write import write_binary_stl

SCRIPTS = Path(__file__).resolve().parents[1]
PREVERSE = SCRIPTS / "preverse_cli.py"


def test_triangle_wrap_refuses_step_write(tmp_path: Path):
    soup = tmp_path / "soup.step"
    soup.write_text(triangle_soup_step(100), encoding="utf-8")
    dest = tmp_path / "step"
    dest.mkdir()
    refused, msg = refuse_triangle_wrap(soup, input_triangles=100, dest_dir=dest)
    assert refused is True
    assert "triangle-wrapped" in msg
    assert list(dest.glob("*.step")) == []


def test_force_open_mesh_does_not_write_step_or_stl(tmp_path: Path):
    stl = tmp_path / "open.stl"
    write_binary_stl(stl, cube_tris(20.0)[:-1])
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
            "open",
            "--force",
        ],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode != 0
    assert not (tmp_path / "step" / "open.step").exists()
    # --force may write IR but must not deliver STEP/STL
    assert not (tmp_path / "stl" / "open.stl").exists()


def test_compare_cube_within_budget(tmp_path: Path):
    from extract_sketches import apply_sketches
    from hypothesize_features import hypothesize_features
    from compare_deviation import compare_meshes
    from segment_surfaces import apply_segment, load_aligned_mesh
    from tessellate_solid import tessellate_ir

    stl = tmp_path / "cube.stl"
    write_binary_stl(stl, cube_tris(20.0))
    ir, code = analyze_stl(stl, body="cube")
    assert code == 0
    mesh = load_aligned_mesh(stl, ir)
    ir = hypothesize_features(apply_sketches(apply_segment(ir, mesh), mesh))
    tris = tessellate_ir(ir)
    report = compare_meshes(stl, tris, ir)
    assert report["pass"] is True
    assert report["max"] <= ir["tolerance"]["max_deviation_mm"]
    for key in ("max", "mean", "p95", "n", "max_deviation_mm", "pass"):
        assert key in report
