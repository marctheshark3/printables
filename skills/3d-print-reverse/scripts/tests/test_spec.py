from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from emit_print_spec import spec_from_ir, write_print_spec
from extract_sketches import apply_sketches
from hypothesize_features import hypothesize_features
from mesh_analyze import analyze_stl
from mesh_fixtures import cube_tris
from segment_surfaces import apply_segment, load_aligned_mesh
from stl_write import write_binary_stl

REPO = Path(__file__).resolve().parents[4]
BRIEF = REPO / "skills" / "3d-print-design-brief" / "scripts"
sys.path.insert(0, str(BRIEF))
import print_spec as print_spec_mod  # noqa: E402


def test_spec_emit_matches_ir_parameters(tmp_path: Path):
    stl = tmp_path / "cube.stl"
    write_binary_stl(stl, cube_tris(20.0))
    ir, _ = analyze_stl(stl, body="cube")
    mesh = load_aligned_mesh(stl, ir)
    ir = hypothesize_features(apply_sketches(apply_segment(ir, mesh), mesh))
    spec = spec_from_ir(ir, kernel="cadquery", part_name="cube-reverse")
    assert spec["cad"]["backend"] == "cadquery"
    assert spec["cad"]["parametric"] is True
    spec_params = {d["parameter"] for d in spec["dimensions"]}
    ir_params = {d["parameter"] for d in ir["dimensions"]}
    assert ir_params == spec_params
    assert spec["reverse"]["class"] == ir["class"]
    path = write_print_spec(tmp_path, spec)
    errors = print_spec_mod.validate(spec)
    assert errors == [], errors
    result = subprocess.run(
        [sys.executable, str(BRIEF / "validate_print_spec.py"), str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
