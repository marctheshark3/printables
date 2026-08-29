from __future__ import annotations

from pathlib import Path

from extract_sketches import apply_sketches
from hypothesize_features import hypothesize_features
from mesh_analyze import analyze_stl
from mesh_fixtures import cube_tris, plate_with_hole_tris
from segment_surfaces import apply_segment, load_aligned_mesh
from stl_write import write_binary_stl


def _pipeline(tmp_path: Path, tris, body: str):
    stl = tmp_path / f"{body}.stl"
    write_binary_stl(stl, tris)
    ir, code = analyze_stl(stl, body=body)
    assert code == 0
    mesh = load_aligned_mesh(stl, ir)
    ir = apply_segment(ir, mesh)
    ir = apply_sketches(ir, mesh)
    ir = hypothesize_features(ir)
    return ir


def test_cube_is_one_extrude(tmp_path: Path):
    ir = _pipeline(tmp_path, cube_tris(20.0), "cube")
    types = [f["type"] for f in ir["features"]]
    assert types.count("extrude") == 1
    extrude = next(f for f in ir["features"] if f["type"] == "extrude")
    assert abs(float(extrude["depth_mm"]) - 20.0) < 1e-3
    assert ir["class"] == "parametric"
    assert ir["regions"]["plane"] == 6


def test_plate_hole_is_extrude_and_cylinder(tmp_path: Path):
    ir = _pipeline(tmp_path, plate_with_hole_tris(), "plate")
    types = [f["type"] for f in ir["features"]]
    assert "extrude" in types
    assert "hole" in types
    assert ir["regions"]["cylinder"] >= 1
    hole = next(f for f in ir["features"] if f["type"] == "hole")
    assert abs(float(hole["diameter_mm"]) - 10.0) < 0.2
