#!/usr/bin/env python3
"""Emit a fit coupon whose named parameters match PRINT_SPEC.yaml."""
from __future__ import annotations

import argparse
import math
import struct
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from print_spec import load_spec  # noqa: E402

Vec3 = Tuple[float, float, float]
Tri = Tuple[Vec3, Vec3, Vec3]
COUPON_XY_MM = 20.0
COUPON_Z_MM = 3.2
HOLE_SEGMENTS = 32


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def add_quad(tris: List[Tri], a: Vec3, b: Vec3, c: Vec3, d: Vec3, outward: Vec3) -> None:
    n = _cross(_sub(b, a), _sub(c, a))
    if _dot(n, outward) >= 0:
        tris.append((a, b, c))
        tris.append((a, c, d))
    else:
        tris.append((a, c, b))
        tris.append((a, d, c))


def write_binary_stl(path: Path, triangles: Sequence[Tri]) -> None:
    data = bytearray(80)
    data.extend(struct.pack("<I", len(triangles)))
    for a, b, c in triangles:
        data.extend(struct.pack("<12fH", 0, 0, 0, *a, *b, *c, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def hole_parameter_and_diameter(spec) -> tuple[str | None, float]:
    hole_param = None
    hole_d = None
    for dim in spec.dimensions:
        blob = f"{dim.name} {dim.parameter}".lower()
        if "hole" in blob or blob.endswith("_d") or "diameter" in blob:
            hole_param = dim.parameter
            hole_d = float(dim.value_mm)
            break
    if hole_d is None:
        hole_d = 3.4
    return hole_param, hole_d + 2.0 * float(spec.clearance_per_side_mm)


def ray_to_square(cx: float, cy: float, dx: float, dy: float, hi: float) -> tuple[float, float]:
    ts: list[float] = []
    if abs(dx) > 1e-12:
        for edge in (0.0, hi):
            t = (edge - cx) / dx
            if t > 1e-12:
                y = cy + t * dy
                if -1e-9 <= y <= hi + 1e-9:
                    ts.append(t)
    if abs(dy) > 1e-12:
        for edge in (0.0, hi):
            t = (edge - cy) / dy
            if t > 1e-12:
                x = cx + t * dx
                if -1e-9 <= x <= hi + 1e-9:
                    ts.append(t)
    t = min(ts)
    return (cx + t * dx, cy + t * dy)


def plate_with_hole(xy: float, z: float, hole_d: float, segments: int = HOLE_SEGMENTS) -> List[Tri]:
    """Square plate with a through-hole. One watertight shell."""
    if hole_d <= 0 or hole_d >= xy:
        raise SystemExit(f"HARD: coupon hole {hole_d} mm does not fit plate {xy} mm")
    r = hole_d / 2.0
    cx = cy = xy / 2.0
    inners: list[tuple[float, float]] = []
    outers: list[tuple[float, float]] = []
    for i in range(segments):
        theta = -math.pi / 4.0 + 2.0 * math.pi * i / segments
        dx, dy = math.cos(theta), math.sin(theta)
        inners.append((cx + r * dx, cy + r * dy))
        outers.append(ray_to_square(cx, cy, dx, dy, xy))
    tris: List[Tri] = []
    for i in range(segments):
        j = (i + 1) % segments
        ix0, iy0 = inners[i]
        ix1, iy1 = inners[j]
        ox0, oy0 = outers[i]
        ox1, oy1 = outers[j]
        add_quad(
            tris,
            (ox0, oy0, z),
            (ox1, oy1, z),
            (ix1, iy1, z),
            (ix0, iy0, z),
            (0.0, 0.0, 1.0),
        )
        add_quad(
            tris,
            (ox0, oy0, 0.0),
            (ix0, iy0, 0.0),
            (ix1, iy1, 0.0),
            (ox1, oy1, 0.0),
            (0.0, 0.0, -1.0),
        )
        add_quad(
            tris,
            (ix0, iy0, z),
            (ix1, iy1, z),
            (ix1, iy1, 0.0),
            (ix0, iy0, 0.0),
            (cx - ix0, cy - iy0, 0.0),
        )
        mx = (oy1 - oy0)
        my = (ox0 - ox1)
        add_quad(
            tris,
            (ox0, oy0, 0.0),
            (ox1, oy1, 0.0),
            (ox1, oy1, z),
            (ox0, oy0, z),
            (mx, my, 0.0),
        )
    return tris


def coupon_paths(spec) -> tuple[Path, Path]:
    coupon = spec.fit_coupon
    if isinstance(coupon, str) and coupon.endswith(".stl"):
        stl_rel = coupon
    else:
        stl_rel = f"fit/{spec.part_name}-coupon.stl"
    stl = Path(stl_rel)
    scad = stl.with_suffix(".scad")
    return stl, scad


def scad_source(spec) -> str:
    hole_param, _bore = hole_parameter_and_diameter(spec)
    lines = [
        "// Fit coupon generated from PRINT_SPEC.yaml. Units: millimetres.",
        f"clearance_per_side_mm = {spec.clearance_per_side_mm};",
        f"coupon_size_mm = {COUPON_XY_MM};",
        f"coupon_z_mm = {COUPON_Z_MM};",
        "$fn = 32;",
        "eps = 0.02;",
        "",
    ]
    for dim in spec.dimensions:
        lines.append(f"{dim.parameter} = {dim.value_mm};")
    lines.append("")
    hole_expr = hole_param if hole_param else "3.4"
    lines.extend(
        [
            "difference() {",
            "  cube([coupon_size_mm, coupon_size_mm, coupon_z_mm]);",
            "  translate([coupon_size_mm / 2, coupon_size_mm / 2, -eps])",
            f"    cylinder(d = {hole_expr} + 2 * clearance_per_side_mm, h = coupon_z_mm + 2 * eps);",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a fit coupon from PRINT_SPEC")
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    spec, errors = load_spec(project / "docs" / "PRINT_SPEC.yaml", project=project)
    if spec is None or errors:
        for error in errors:
            print(f"HARD: {error}")
        return 1
    if not spec.fit_required:
        print("HARD: generate_coupon requires fit.required: true")
        return 1
    stl_rel, scad_rel = coupon_paths(spec)
    scad_path = project / scad_rel
    stl_path = project / stl_rel
    scad_path.parent.mkdir(parents=True, exist_ok=True)
    scad_path.write_text(scad_source(spec), encoding="utf-8")
    _param, bore = hole_parameter_and_diameter(spec)
    write_binary_stl(stl_path, plate_with_hole(COUPON_XY_MM, COUPON_Z_MM, bore))
    print(f"COUPON_SCAD: {scad_rel.as_posix()}")
    print(f"COUPON_STL: {stl_rel.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
