from __future__ import annotations

import json
from pathlib import Path

from ir_io import dumps_ir, load_ir
from mesh_analyze import analyze_stl
from mesh_common import load_mesh, pca_aabb_alignment, transform_mesh
from mesh_fixtures import cube_tris, plate_with_hole_tris
from segment_surfaces import apply_segment, load_aligned_mesh, segment_mesh
from stl_write import write_binary_stl


def test_cube_segments_six_planes(tmp_path: Path):
    stl = tmp_path / "cube.stl"
    write_binary_stl(stl, cube_tris(20.0))
    ir, code = analyze_stl(stl, body="cube")
    assert code == 0
    assert ir["units"] == "mm"
    assert ir["topology"]["boundary_edges"] == 0
    assert ir["topology"]["nonmanifold_edges"] == 0
    mesh = load_aligned_mesh(stl, ir)
    ir = apply_segment(ir, mesh)
    assert ir["regions"]["plane"] == 6
    assert ir["regions"]["cylinder"] == 0
    assert ir["regions"]["fallback"] == 0


def test_plate_hole_has_cylinder(tmp_path: Path):
    stl = tmp_path / "plate.stl"
    write_binary_stl(stl, plate_with_hole_tris())
    ir, code = analyze_stl(stl, body="plate")
    assert code == 0
    mesh = load_aligned_mesh(stl, ir)
    ir = apply_segment(ir, mesh)
    assert ir["regions"]["plane"] >= 2
    assert ir["regions"]["cylinder"] >= 1


def test_alignment_stable_on_world_cube(tmp_path: Path):
    stl = tmp_path / "cube.stl"
    write_binary_stl(stl, cube_tris(20.0, origin=(3.0, -4.0, 5.0)))
    ir1, _ = analyze_stl(stl, body="cube")
    ir2, _ = analyze_stl(stl, body="cube")
    assert ir1["alignment"]["rotation_rpy_deg"] == ir2["alignment"]["rotation_rpy_deg"]
    rpy = ir1["alignment"]["rotation_rpy_deg"]
    assert all(abs(v) < 1e-6 for v in rpy)


def test_sorted_json_identity(tmp_path: Path):
    stl = tmp_path / "cube.stl"
    write_binary_stl(stl, cube_tris(20.0))
    ir1, _ = analyze_stl(stl, body="cube")
    mesh = load_aligned_mesh(stl, ir1)
    ir1 = apply_segment(ir1, mesh)
    text1 = dumps_ir(ir1)
    ir2, _ = analyze_stl(stl, body="cube")
    mesh2 = load_aligned_mesh(stl, ir2)
    ir2 = apply_segment(ir2, mesh2)
    text2 = dumps_ir(ir2)
    assert text1 == text2
    a = json.loads(text1)
    b = json.loads(text2)
    assert a == b


def test_open_mesh_hard_without_force(tmp_path: Path):
    tris = cube_tris(20.0)[:-1]
    stl = tmp_path / "open.stl"
    write_binary_stl(stl, tris)
    ir, code = analyze_stl(stl, body="open", force=False)
    assert code == 2
    assert ir["class"] == "failed"


def test_inverted_volume_hard_without_force(tmp_path: Path):
    tris = [(a, c, b) for a, b, c in cube_tris(20.0)]
    stl = tmp_path / "inverted.stl"
    write_binary_stl(stl, tris)
    ir, code = analyze_stl(stl, body="inverted", force=False)
    assert code == 2
    assert ir["class"] == "failed"
    assert any("volume" in w for w in ir["warnings"])
    assert ir["topology"]["volume_mm3"] < 0


def test_units_inch_scales_once(tmp_path: Path):
    stl = tmp_path / "cube.stl"
    write_binary_stl(stl, cube_tris(1.0))
    ir, code = analyze_stl(stl, body="cube", units="inch")
    assert code == 0
    width = next(d for d in ir["dimensions"] if d["parameter"] == "width_mm")
    assert abs(width["raw_mm"] - 25.4) < 1e-3
