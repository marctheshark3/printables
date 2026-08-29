"""Planar sections: 2D line / arc / circle from region boundaries."""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from geom import (
    Vec2,
    Vec3,
    angle_deg,
    plane_basis,
    plane_name,
    project_to_plane,
    vadd,
    vdot,
    vnorm,
    vscale,
    vsub,
    vdist,
)
from ir_io import r6
from mesh_common import TriMesh

Vec2 = Tuple[float, float]


def _boundary_loops(mesh: TriMesh, faces: Sequence[int]) -> List[List[int]]:
    face_set = set(faces)
    edge_count: Dict[Tuple[int, int], int] = defaultdict(int)
    directed: Dict[Tuple[int, int], Tuple[int, int]] = {}
    for fi in faces:
        a, b, c = mesh.faces[fi]
        for u, v in ((a, b), (b, c), (c, a)):
            key = (u, v) if u < v else (v, u)
            edge_count[key] += 1
            if key not in directed:
                directed[key] = (u, v)
            # keep the winding from a face in the region
            if fi in face_set:
                directed[key] = (u, v)
    boundary = [directed[k] for k, n in edge_count.items() if n == 1]
    remaining = list(boundary)
    start_of = defaultdict(list)
    for i, (u, v) in enumerate(remaining):
        start_of[u].append(i)
    used = [False] * len(remaining)
    loops: List[List[int]] = []
    for i, (u, v) in enumerate(remaining):
        if used[i]:
            continue
        loop = [u]
        used[i] = True
        cur = v
        guard = 0
        while cur != u and guard < len(remaining) + 2:
            loop.append(cur)
            nxt = None
            for j, (a, b) in enumerate(remaining):
                if used[j]:
                    continue
                if a == cur:
                    nxt = b
                    used[j] = True
                    break
                if b == cur:
                    nxt = a
                    used[j] = True
                    break
            if nxt is None:
                break
            cur = nxt
            guard += 1
        if len(loop) >= 3:
            loops.append(loop)
    return loops


def _shoelace(poly: Sequence[Vec2]) -> float:
    acc = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        acc += x1 * y2 - x2 * y1
    return 0.5 * acc


def _circle_fit(pts: Sequence[Vec2]) -> tuple[Vec2, float, float] | None:
    if len(pts) < 5:
        return None
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    rs = [math.hypot(p[0] - cx, p[1] - cy) for p in pts]
    r = sum(rs) / len(rs)
    if r < 1e-9:
        return None
    max_dev = max(abs(x - r) for x in rs)
    return (cx, cy), r, max_dev


def _collinear_dev(pts: Sequence[Vec2]) -> float:
    if len(pts) < 2:
        return 0.0
    ax, ay = pts[0]
    bx, by = pts[-1]
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length < 1e-12:
        return max(math.hypot(p[0] - ax, p[1] - ay) for p in pts)
    max_dev = 0.0
    for px, py in pts:
        max_dev = max(max_dev, abs((px - ax) * dy - (py - ay) * dx) / length)
    return max_dev


def _entities_from_loop(pts: Sequence[Vec2], fit_mm: float) -> list[dict[str, Any]]:
    circ = _circle_fit(pts)
    if circ is not None and circ[2] <= fit_mm:
        (cx, cy), r, _dev = circ
        return [
            {
                "type": "circle",
                "center_mm": [r6(cx), r6(cy)],
                "radius_mm": r6(r),
            }
        ]
    n = len(pts)
    if n < 3:
        return [{"type": "polyline", "points_mm": [[r6(p[0]), r6(p[1])] for p in pts]}]
    # Split into collinear runs.
    runs: list[list[int]] = []
    current = [0, 1]
    for i in range(2, n + 1):
        idx = i % n
        trial = current + [idx]
        pts_trial = [pts[j] for j in trial]
        if _collinear_dev(pts_trial) <= fit_mm:
            current = trial
        else:
            runs.append(current)
            current = [current[-1], idx]
    if current:
        # merge last into first if they share the closing vertex
        if runs and current[-1] % n == runs[0][0]:
            runs[0] = current[:-1] + runs[0]
        else:
            runs.append(current)
    entities: list[dict[str, Any]] = []
    if len(runs) >= 3 and all(_collinear_dev([pts[j] for j in run]) <= fit_mm for run in runs):
        for run in runs:
            a, b = pts[run[0]], pts[run[-1]]
            entities.append(
                {
                    "type": "line",
                    "a_mm": [r6(a[0]), r6(a[1])],
                    "b_mm": [r6(b[0]), r6(b[1])],
                }
            )
        return entities
    return [{"type": "polyline", "points_mm": [[r6(p[0]), r6(p[1])] for p in pts]}]


def extract_sketches(
    mesh: TriMesh,
    regions: Sequence[dict[str, Any]],
    face_ids: Sequence[Sequence[int]],
    *,
    fit_mm: float = 0.05,
    min_area_frac: float = 0.04,
) -> list[dict[str, Any]]:
    total_area = sum(float(r.get("area_mm2") or 0.0) for r in regions) or 1.0
    sketches: list[dict[str, Any]] = []
    sid = 0
    for region, faces in zip(regions, face_ids):
        if region.get("kind") != "plane":
            continue
        if float(region.get("area_mm2") or 0.0) / total_area < min_area_frac:
            continue
        origin = tuple(float(x) for x in region["origin_mm"])  # type: ignore[arg-type]
        normal = tuple(float(x) for x in region["normal"])  # type: ignore[arg-type]
        x_axis, y_axis = plane_basis(normal)  # type: ignore[arg-type]
        loops = _boundary_loops(mesh, faces)
        projected: list[tuple[float, list[Vec2], list[int]]] = []
        for loop in loops:
            pts2 = [
                project_to_plane(mesh.vertices[i], origin, normal, x_axis, y_axis)  # type: ignore[arg-type]
                for i in loop
            ]
            area = abs(_shoelace(pts2))
            projected.append((area, pts2, loop))
        if not projected:
            continue
        projected.sort(key=lambda item: -item[0])
        outer_area, outer_pts, _outer_ids = projected[0]
        if _shoelace(outer_pts) < 0:
            outer_pts = list(reversed(outer_pts))
        profiles = [
            {
                "id": "outer",
                "role": "outer",
                "entities": _entities_from_loop(outer_pts, fit_mm),
            }
        ]
        hole_i = 0
        for area, pts, _ids in projected[1:]:
            if area < fit_mm * fit_mm:
                continue
            if _shoelace(pts) > 0:
                pts = list(reversed(pts))
            hole_i += 1
            profiles.append(
                {
                    "id": f"hole_{hole_i}",
                    "role": "hole",
                    "entities": _entities_from_loop(pts, fit_mm),
                }
            )
        sid += 1
        sketches.append(
            {
                "id": f"s{sid}",
                "plane": plane_name(normal, origin),  # type: ignore[arg-type]
                "origin_mm": [r6(x) for x in origin],
                "normal": [r6(x) for x in normal],
                "x_axis": [r6(x) for x in x_axis],
                "y_axis": [r6(x) for x in y_axis],
                "region_id": region["id"],
                "area_mm2": r6(outer_area),
                "profiles": profiles,
            }
        )
    sketches.sort(key=lambda s: (-float(s["area_mm2"]), s["id"]))
    return sketches


def apply_sketches(ir: dict[str, Any], mesh: TriMesh) -> dict[str, Any]:
    regions = ir.get("region_list") or []
    face_ids = ir.get("_segment_face_ids") or [[] for _ in regions]
    fit_mm = float(ir.get("tolerance", {}).get("fit_mm", 0.05))
    ir["sketches"] = extract_sketches(mesh, regions, face_ids, fit_mm=fit_mm)
    return ir
