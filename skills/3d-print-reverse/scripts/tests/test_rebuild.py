from __future__ import annotations

from pathlib import Path

from extract_sketches import apply_sketches
from geom import vadd, vcross, vdist, vscale
from hypothesize_features import hypothesize_features
from ir_io import load_ir
from mesh_analyze import analyze_stl
from mesh_fixtures import cube_tris, plate_with_hole_tris
from rebuild_cad import (
    _outer_uv,
    cadquery_plane_frame,
    emit_cadquery_source,
    emit_vibecad_source,
)
from segment_surfaces import apply_segment, load_aligned_mesh
from stl_write import write_binary_stl
from tessellate_solid import tessellate_ir

REPO = Path(__file__).resolve().parents[4]


def _ir(tmp_path: Path, tris, body: str = "cube"):
    stl = tmp_path / f"{body}.stl"
    write_binary_stl(stl, tris)
    ir, _ = analyze_stl(stl, body=body)
    mesh = load_aligned_mesh(stl, ir)
    return hypothesize_features(apply_sketches(apply_segment(ir, mesh), mesh))


def test_kernel_source_runs_under_freecadcmd_stem_name(tmp_path: Path):
    ir = _ir(tmp_path, cube_tris(20.0), "cube")
    cq = emit_cadquery_source(ir)
    vc = emit_vibecad_source(ir)
    for src in (cq, vc):
        assert "if __name__ in {'__main__', Path(__file__).stem}:" in src
        assert "if __name__ == '__main__':" not in src


def test_rebuild_source_contains_named_mm_parameters(tmp_path: Path):
    ir = _ir(tmp_path, cube_tris(20.0), "cube")
    cq = emit_cadquery_source(ir)
    vc = emit_vibecad_source(ir)
    for param in (d["parameter"] for d in ir["dimensions"]):
        assert f"{param} =" in cq
        assert f"{param} =" in vc
    assert "cadquery" in cq
    assert "import cadquery" not in open(
        Path(__file__).resolve().parents[1] / "preverse_cli.py", encoding="utf-8"
    ).read().split("def ")[0]


def test_rebuild_source_extrudes_ir_profile_not_aabb_box(tmp_path: Path):
    ir = _ir(tmp_path, cube_tris(20.0), "cube")
    cq = emit_cadquery_source(ir)
    vc = emit_vibecad_source(ir)
    assert "box(width_mm, depth_mm, height_mm)" not in cq
    assert ".extrude(" in cq
    assert "Part.makeBox" not in vc
    assert "Part.makePolygon" in vc or "Part.Face" in vc
    assert "extrude" in vc


def test_rebuild_holes_use_named_uv_not_face_center(tmp_path: Path):
    ir = _ir(tmp_path, plate_with_hole_tris(), "plate")
    cq = emit_cadquery_source(ir)
    vc = emit_vibecad_source(ir)
    holes = [f for f in ir["features"] if f.get("type") == "hole"]
    assert holes, ir["features"]
    hid = holes[0]["id"]
    assert f"hole_{hid}_u_mm" in cq
    assert f"hole_{hid}_v_mm" in cq
    assert f"hole_{hid}_d_mm" in cq
    assert "faces('>Z').workplane().hole(" not in cq
    assert f"moveTo(hole_{hid}_u_mm, hole_{hid}_v_mm)" in cq
    assert f"x_axis * hole_{hid}_u_mm" in vc
    assert f"y_axis * hole_{hid}_v_mm" in vc
    assert "makeCylinder" in vc


def test_coupon_ir_kernel_source_is_l_profile_not_block():
    ir = load_ir(REPO / "examples/bracket-coupon-reverse/reverse/bracket.ir.json")
    cq = emit_cadquery_source(ir)
    vc = emit_vibecad_source(ir)
    assert "box(width_mm, depth_mm, height_mm)" not in cq
    assert "Part.makeBox" not in vc
    assert "lineTo" in cq
    assert "Part.makePolygon" in vc
    assert "hole_f2_u_mm" in cq
    assert "hole_f3_u_mm" in cq
    assert "hole_f4_u_mm" in cq
    assert "moveTo(hole_f2_u_mm, hole_f2_v_mm)" in cq
    assert cq.count("solid.cut(cutter)") == 3
    assert vc.count("solid.cut(cutter)") == 3


def test_cadquery_plane_preserves_sketch_uv():
    """CadQuery yDir = normal × xDir must match sketch y_axis (no UV mirror)."""
    ir = load_ir(REPO / "examples/bracket-coupon-reverse/reverse/bracket.ir.json")
    sketch = next(s for s in ir["sketches"] if s["id"] == "s1")
    feat = next(f for f in ir["features"] if f.get("type") == "extrude")
    xDir, zDir, sign = cadquery_plane_frame(sketch, feat.get("direction"))
    yDir = vcross(zDir, xDir)
    origin = tuple(float(c) for c in sketch["origin_mm"])
    x_axis = tuple(float(c) for c in sketch["x_axis"])
    y_axis = tuple(float(c) for c in sketch["y_axis"])
    fit = float(ir["tolerance"]["fit_mm"])

    def cq_pt(u: float, v: float):
        return vadd(origin, vadd(vscale(xDir, u), vscale(yDir, v)))

    def ir_pt(u: float, v: float):
        return vadd(origin, vadd(vscale(x_axis, u), vscale(y_axis, v)))

    # Coupon s1_p0: old Plane.normal=direction mirrored this by ~35.6 mm.
    u0, v0 = -16.527843, -17.807164
    assert vdist(cq_pt(u0, v0), ir_pt(u0, v0)) <= fit + 1e-9
    for u, v in _outer_uv(sketch):
        assert vdist(cq_pt(u, v), ir_pt(u, v)) <= fit + 1e-9
    assert sign == -1.0
    cq = emit_cadquery_source(ir)
    assert "normal=cq.Vector(0.000000, 0.000000, 1.000000)" in cq
    assert "normal=cq.Vector(-0.000000, -0.000000, -1.000000)" not in cq
    assert "extrude(-1.0 * float(extrude_depth_mm))" in cq
    assert "extrude(-1.0 * (float(extrude_depth_mm) + 2.0))" in cq


def test_named_parameter_change_regenerates_stl(tmp_path: Path):
    ir = _ir(tmp_path, cube_tris(20.0), "cube")
    tris0 = tessellate_ir(ir)
    for dim in ir["dimensions"]:
        if dim["parameter"] == "width_mm":
            dim["value_mm"] = 40.0
    tris1 = tessellate_ir(ir)
    from stl_io import bbox_and_volume

    mn0, mx0, _ = bbox_and_volume(tris0)
    mn1, mx1, _ = bbox_and_volume(tris1)
    spans0 = [mx0[i] - mn0[i] for i in range(3)]
    spans1 = [mx1[i] - mn1[i] for i in range(3)]
    assert min(abs(s - 20.0) for s in spans0) < 0.2
    assert min(abs(s - 40.0) for s in spans1) < 0.2
