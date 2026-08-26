"""Assembled occupancy, joint sweep, and one handbook-style section check.

L1/L2 reuse triangle occupancy from overlap.py. L3 is not FEA: it compares
annular hub torsion tau = T / Wp against a conservative printed-plastic
allowable times the declared safety_factor.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Iterable

BRIEF_SCRIPTS = Path(__file__).resolve().parent.parent.parent / "3d-print-design-brief" / "scripts"
if str(BRIEF_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(BRIEF_SCRIPTS))

from overlap import occupancies_illegal, tris_aabb
from print_spec import AssemblyBody, PrintSpec, load_spec
from print_spec_assembly import required_load_errors
from stl_io import Tri, load_binary_stl

Vec3 = tuple[float, float, float]

# Handbook-style conservative shear allowables for printed plastic (MPa). Not FEA.
ALLOWABLE_SHEAR_MPA = {
    "PETG": 15.0,
    "PLA": 12.0,
    "ABS": 15.0,
}
REVOLUTE_STEP_DEG = 45.0


def rpy_matrix(rpy_deg: Iterable[float]) -> tuple[Vec3, Vec3, Vec3]:
    """URDF R = Rz(yaw) @ Ry(pitch) @ Rx(roll), angles in degrees."""
    roll, pitch, yaw = (math.radians(float(a)) for a in rpy_deg)
    cx, sx = math.cos(roll), math.sin(roll)
    cy, sy = math.cos(pitch), math.sin(pitch)
    cz, sz = math.cos(yaw), math.sin(yaw)
    # Rx
    r00 = cy * cz
    r01 = cz * sy * sx - sz * cx
    r02 = cz * sy * cx + sz * sx
    r10 = cy * sz
    r11 = sz * sy * sx + cz * cx
    r12 = sz * sy * cx - cz * sx
    r20 = -sy
    r21 = cy * sx
    r22 = cy * cx
    return ((r00, r01, r02), (r10, r11, r12), (r20, r21, r22))


def _apply(matrix: tuple[Vec3, Vec3, Vec3], translation: Vec3, point: Vec3) -> Vec3:
    x, y, z = point
    return (
        matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * z + translation[0],
        matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * z + translation[1],
        matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * z + translation[2],
    )


def transform_tris(tris: list[Tri], xyz_mm: Vec3, rpy_deg: Vec3) -> list[Tri]:
    matrix = rpy_matrix(rpy_deg)
    return [
        (_apply(matrix, xyz_mm, a), _apply(matrix, xyz_mm, b), _apply(matrix, xyz_mm, c))
        for a, b, c in tris
    ]


def box_triangles(sx: float, sy: float, sz: float) -> list[Tri]:
    p = [
        (0.0, 0.0, 0.0), (sx, 0.0, 0.0), (sx, sy, 0.0), (0.0, sy, 0.0),
        (0.0, 0.0, sz), (sx, 0.0, sz), (sx, sy, sz), (0.0, sy, sz),
    ]
    faces = [
        (0, 2, 1), (0, 3, 2),
        (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4),
        (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6),
        (3, 0, 4), (3, 4, 7),
    ]
    return [(p[a], p[b], p[c]) for a, b, c in faces]


def _normalize(axis: Vec3) -> Vec3:
    length = math.sqrt(axis[0] ** 2 + axis[1] ** 2 + axis[2] ** 2) or 1.0
    return (axis[0] / length, axis[1] / length, axis[2] / length)


def rotate_around_axis(point: Vec3, origin: Vec3, axis: Vec3, angle_deg: float) -> Vec3:
    ux, uy, uz = _normalize(axis)
    px = point[0] - origin[0]
    py = point[1] - origin[1]
    pz = point[2] - origin[2]
    theta = math.radians(angle_deg)
    c, s = math.cos(theta), math.sin(theta)
    d = (1.0 - c)
    # Rodrigues
    rx = (
        (c + ux * ux * d) * px
        + (ux * uy * d - uz * s) * py
        + (ux * uz * d + uy * s) * pz
    )
    ry = (
        (uy * ux * d + uz * s) * px
        + (c + uy * uy * d) * py
        + (uy * uz * d - ux * s) * pz
    )
    rz = (
        (uz * ux * d - uy * s) * px
        + (uz * uy * d + ux * s) * py
        + (c + uz * uz * d) * pz
    )
    return (rx + origin[0], ry + origin[1], rz + origin[2])


def rotate_tris_around(tris: list[Tri], origin: Vec3, axis: Vec3, angle_deg: float) -> list[Tri]:
    return [
        (
            rotate_around_axis(a, origin, axis, angle_deg),
            rotate_around_axis(b, origin, axis, angle_deg),
            rotate_around_axis(c, origin, axis, angle_deg),
        )
        for a, b, c in tris
    ]


def sweep_angles(min_deg: float, max_deg: float, step_deg: float = REVOLUTE_STEP_DEG) -> list[float]:
    if max_deg < min_deg:
        min_deg, max_deg = max_deg, min_deg
    angles = [float(min_deg)]
    cursor = min_deg + step_deg
    while cursor < max_deg - 1e-9:
        angles.append(float(cursor))
        cursor += step_deg
    if abs(max_deg - min_deg) > 1e-9:
        angles.append(float(max_deg))
    # 0 and 360 are the same rest pose
    unique: list[float] = []
    seen: set[float] = set()
    span = max_deg - min_deg
    for angle in angles:
        key = round(angle % 360.0, 6) if span >= 360.0 - 1e-9 else round(angle, 6)
        if key in seen:
            continue
        seen.add(key)
        unique.append(angle)
    return unique


def polar_section_modulus_m3(outer_mm: float, inner_mm: float) -> float | None:
    ro = outer_mm / 1000.0
    ri = inner_mm / 1000.0
    if ro <= 0 or ri < 0 or ro <= ri:
        return None
    return math.pi * (ro ** 4 - ri ** 4) / (2.0 * ro)


def moment_to_n_m(magnitude: float, units: str) -> float | None:
    key = units.strip().lower().replace(" ", "").replace("-", "_").replace("/", "_")
    if key in {"n_m", "nm", "n.m"}:
        return float(magnitude)
    if key in {"n_mm", "nmm"}:
        return float(magnitude) / 1000.0
    if key in {"kg_cm", "kgcm"}:
        return float(magnitude) * 0.0980665
    return None


def _dimension_mm(spec: PrintSpec, *names: str) -> float | None:
    wanted = set(names)
    for dim in spec.dimensions:
        if dim.parameter in wanted or dim.name in wanted:
            return float(dim.value_mm)
    return None


def hub_shear_mpa(moment_n_m: float, outer_mm: float, inner_mm: float) -> float | None:
    wp = polar_section_modulus_m3(outer_mm, inner_mm)
    if wp is None or wp <= 0:
        return None
    return (moment_n_m / wp) / 1e6


def _place_body(
    project: Path,
    body: AssemblyBody,
    stl_by_name: dict[str, str],
    hw_by_id: dict[str, tuple[float, float, float]],
) -> list[Tri]:
    if body.printed_body:
        _normals, tris, _n = load_binary_stl(project / stl_by_name[body.printed_body])
        return transform_tris(tris, body.pose.xyz_mm, body.pose.rpy_deg)
    assert body.hardware_id is not None
    return transform_tris(
        box_triangles(*hw_by_id[body.hardware_id]), body.pose.xyz_mm, body.pose.rpy_deg
    )


def place_assembly(project: Path, spec: PrintSpec) -> dict[str, list[Tri]]:
    stl_by_name = {item.body: item.path for item in spec.stl_files}
    hw_by_id = {item.id: item.envelope_mm for item in spec.hardware}
    return {
        body.id: _place_body(project, body, stl_by_name, hw_by_id)
        for body in spec.assembly_bodies
    }


def _inflated_aabb_box(tris: list[Tri], clearance_mm: float) -> list[Tri]:
    xmin, ymin, zmin, xmax, ymax, zmax = tris_aabb(tris)
    pad = max(clearance_mm, 0.0)
    return transform_tris(
        box_triangles(
            (xmax - xmin) + 2 * pad,
            (ymax - ymin) + 2 * pad,
            (zmax - zmin) + 2 * pad,
        ),
        (xmin - pad, ymin - pad, zmin - pad),
        (0.0, 0.0, 0.0),
    )


def l1_occupancy(spec: PrintSpec, placed: dict[str, list[Tri]]) -> list[str]:
    hard: list[str] = []
    ids = [body.id for body in spec.assembly_bodies]
    for i, a_id in enumerate(ids):
        for b_id in ids[i + 1 :]:
            if not occupancies_illegal(placed[a_id], placed[b_id]):
                continue
            hard.append(f"L1 collision: {a_id} intersects {b_id}")
    for joint in spec.joints:
        parent = placed.get(joint.parent)
        child = placed.get(joint.child)
        if parent is None or child is None:
            continue
        if occupancies_illegal(parent, child):
            continue
        inflated = _inflated_aabb_box(child, joint.clearance_per_side_mm)
        if occupancies_illegal(inflated, parent):
            hard.append(
                f"L1 clearance: joint {joint.id} {joint.parent}/{joint.child} "
                f"below {joint.clearance_per_side_mm} mm per side"
            )
    return hard


def l2_sweep(spec: PrintSpec, placed: dict[str, list[Tri]]) -> list[str]:
    hard: list[str] = []
    others_index = dict(placed)
    for joint in spec.joints:
        if joint.type != "revolute" or joint.limits is None:
            continue
        child = placed.get(joint.child)
        origin_body = next((b for b in spec.assembly_bodies if b.id == joint.child), None)
        if child is None or origin_body is None:
            hard.append(f"L2 joint {joint.id} child {joint.child} is not placed")
            continue
        origin = origin_body.pose.xyz_mm
        for angle in sweep_angles(joint.limits[0], joint.limits[1]):
            if abs(angle - joint.limits[0]) < 1e-9:
                posed = child
            else:
                posed = rotate_tris_around(child, origin, joint.axis, angle - joint.limits[0])
            for other_id, other in others_index.items():
                if other_id == joint.child:
                    continue
                if occupancies_illegal(posed, other):
                    hard.append(
                        f"L2 self-collision: joint {joint.id} at {angle:g} deg "
                        f"({joint.child} vs {other_id})"
                    )
                    break
            else:
                continue
            break
    return hard


def l3_loads(spec: PrintSpec) -> list[str]:
    hard: list[str] = []
    material = str(spec.material).upper()
    allowable = ALLOWABLE_SHEAR_MPA.get(material)
    hard.extend(
        required_load_errors(
            product_class=spec.product_class,
            has_assembly_bodies=bool(spec.assembly_bodies),
            revolute_children=[j.child for j in spec.joints if j.type == "revolute"],
            load_kinds=[load.kind for load in spec.loads],
            moment_targets={load.target for load in spec.loads if load.kind == "moment"},
        )
    )
    for load in spec.loads:
        if load.source == "assumed":
            hard.append(f"L3 load {load.id} source cannot be assumed")
        if load.kind != "moment":
            continue
        if allowable is None:
            hard.append(f"L3 no conservative allowable for material {spec.material}")
            continue
        moment = moment_to_n_m(load.magnitude, load.units)
        if moment is None:
            hard.append(f"L3 load {load.id} units {load.units} are not a supported moment unit")
            continue
        outer = _dimension_mm(spec, load.section_outer) if load.section_outer else None
        inner = _dimension_mm(spec, load.section_inner) if load.section_inner else None
        if outer is None or inner is None:
            hard.append(
                f"L3 load {load.id} needs section.outer_parameter and section.inner_parameter "
                "naming dimensions"
            )
            continue
        tau = hub_shear_mpa(moment, outer, inner)
        if tau is None:
            hard.append(f"L3 load {load.id} hub section is invalid")
            continue
        if tau * load.safety_factor > allowable + 1e-9:
            hard.append(
                f"L3 hub shear {tau:.3f} MPa × SF {load.safety_factor:g} exceeds "
                f"{allowable:g} MPa {material} allowable for {load.id}"
            )
    return hard


def audit_assembly(project: Path, spec_rel: str = "docs/PRINT_SPEC.yaml") -> tuple[list[str], list[str], list[str]]:
    spec_path = project / spec_rel
    spec, errors = load_spec(spec_path, project=project, check_files=False)
    if spec is None or errors:
        return [error for error in errors], [], []
    info: list[str] = []
    if not spec.assembly_bodies:
        return [], [], ["no assembly block; occupancy proof skipped"]
    spec, errors = load_spec(spec_path, project=project, check_files=True)
    if spec is None or errors:
        return [error for error in errors], [], []
    placed = place_assembly(project, spec)
    info.append(f"placed {len(placed)} assembled occupancies in {spec.assembly_frame}")
    hard = []
    hard.extend(l1_occupancy(spec, placed))
    hard.extend(l2_sweep(spec, placed))
    hard.extend(l3_loads(spec))
    return hard, [], info
