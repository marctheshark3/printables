"""Two-sided sampled deviation between rebuilt mesh and input STL."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable, List, Sequence

from geom import Tri, Vec3, closest_point_on_triangle, tri_area, vdist, vmean
from ir_io import r6
from mesh_common import (
    WELD_MM,
    load_mesh,
    pca_aabb_alignment,
    rotation_from_ir,
    transform_mesh,
)


def _samples(tris: Sequence[Tri], stride: int = 1) -> list[Vec3]:
    pts: list[Vec3] = []
    for i, (a, b, c) in enumerate(tris):
        if stride > 1 and (i % stride) != 0:
            continue
        pts.append(a)
        pts.append(b)
        pts.append(c)
        pts.append(vmean((a, b, c)))
    return pts


def _min_dist(p: Vec3, tris: Sequence[Tri]) -> float:
    best = 1e99
    for tri in tris:
        q = closest_point_on_triangle(p, tri[0], tri[1], tri[2])
        d = vdist(p, q)
        if d < best:
            best = d
    return best


def two_sided_deviation(
    a_tris: Sequence[Tri],
    b_tris: Sequence[Tri],
    *,
    stride: int | None = None,
    max_samples: int = 400,
) -> dict[str, Any]:
    if stride is None:
        stride = max(1, len(a_tris) // max(1, max_samples // 4))
    sa = _samples(a_tris, stride=stride)
    sb = _samples(b_tris, stride=stride)
    # Cap sample count deterministically (keep first N after stride).
    sa = sa[:max_samples]
    sb = sb[:max_samples]
    dists: list[float] = []
    for p in sa:
        dists.append(_min_dist(p, b_tris))
    for p in sb:
        dists.append(_min_dist(p, a_tris))
    dists.sort()
    n = len(dists)
    if n == 0:
        return {"max": 0.0, "mean": 0.0, "p95": 0.0, "n": 0}
    mean = sum(dists) / n
    p95 = dists[min(n - 1, int(math.ceil(0.95 * n) - 1))]
    return {
        "max": r6(dists[-1]),
        "mean": r6(mean),
        "p95": r6(p95),
        "n": n,
    }


def compare_meshes(
    input_stl: Path,
    rebuilt_tris: Sequence[Tri],
    ir: dict[str, Any],
) -> dict[str, Any]:
    units = "inch" if ir.get("units") == "inch" else "mm"
    # IR is stored in millimetres after scale.
    mesh = load_mesh(input_stl, units="mm" if ir.get("units") == "mm" else "inch", weld=WELD_MM)
    rotation, translation = rotation_from_ir(ir)
    aligned = transform_mesh(mesh, rotation, translation)
    stats = two_sided_deviation(aligned.triangles_xyz(), list(rebuilt_tris))
    budget = float(ir.get("tolerance", {}).get("max_deviation_mm", 0.2))
    stats["max_deviation_mm"] = r6(budget)
    stats["pass"] = bool(stats["max"] <= budget + 1e-9)
    return stats


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = ["max", "mean", "p95", "n", "max_deviation_mm", "pass"]
    ordered = {k: report[k] for k in keys if k in report}
    for k, v in report.items():
        if k not in ordered:
            ordered[k] = v
    path.write_text(json.dumps(ordered, indent=2, sort_keys=False) + "\n", encoding="utf-8")
