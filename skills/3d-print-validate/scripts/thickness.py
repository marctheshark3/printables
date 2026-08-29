"""Sampled inward-ray wall thickness. Not an exact-kernel proof."""
from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from stl_io import Tri, Vec3, tri_area, tri_normal

# HARD if sampled area thinner than min_wall (minus slack) exceeds this fraction.
THIN_WALL_AREA_FRAC = 0.02
# Chorded STLs under-read walls that sit on min_wall_mm; do not HARD that slack.
TESS_SLACK_MM = 0.05
MAX_SAMPLES = 280


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(v: Vec3) -> Vec3:
    length = math.sqrt(_dot(v, v)) or 1.0
    return (v[0] / length, v[1] / length, v[2] / length)


def _centroid(tri: Tri) -> Vec3:
    a, b, c = tri
    return ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0, (a[2] + b[2] + c[2]) / 3.0)


def _unit_normal(stored: Optional[Vec3], tri: Tri) -> Vec3:
    if stored is not None:
        n = stored
        if abs(n[0]) + abs(n[1]) + abs(n[2]) > 1e-9:
            return _norm(n)
    return tri_normal(*tri)


def ray_triangle(orig: Vec3, direction: Vec3, v0: Vec3, v1: Vec3, v2: Vec3) -> Optional[float]:
    """Möller–Trumbore. Returns distance along direction or None."""
    eps = 1e-8
    e1 = _sub(v1, v0)
    e2 = _sub(v2, v0)
    pvec = _cross(direction, e2)
    det = _dot(e1, pvec)
    if abs(det) < eps:
        return None
    inv = 1.0 / det
    tvec = _sub(orig, v0)
    u = _dot(tvec, pvec) * inv
    if u < -eps or u > 1.0 + eps:
        return None
    qvec = _cross(tvec, e1)
    v = _dot(direction, qvec) * inv
    if v < -eps or u + v > 1.0 + eps:
        return None
    t = _dot(e2, qvec) * inv
    if t <= 1e-4:
        return None
    return t


def sample_thickness(
    tris: Sequence[Tri],
    normals: Sequence[Vec3],
    max_samples: int = MAX_SAMPLES,
) -> Tuple[List[Tuple[float, float]], int]:
    """Return ([(area, thickness_mm), ...], n_candidate_faces). Misses are dropped."""
    ranked: List[Tuple[float, int, Vec3]] = []
    for i, tri in enumerate(tris):
        area = tri_area(*tri)
        if area < 1e-8:
            continue
        stored = normals[i] if i < len(normals) else None
        ranked.append((area, i, _unit_normal(stored, tri)))
    ranked.sort(key=lambda item: -item[0])
    if len(ranked) > max_samples:
        step = max(1, len(ranked) // max_samples)
        ranked = ranked[::step][:max_samples]

    hits: List[Tuple[float, float]] = []
    n_tris = len(tris)
    for area, src, n in ranked:
        orig = _add(_centroid(tris[src]), _scale(n, -1e-4))
        direction = (-n[0], -n[1], -n[2])
        best: Optional[float] = None
        for j in range(n_tris):
            if j == src:
                continue
            t = ray_triangle(orig, direction, tris[j][0], tris[j][1], tris[j][2])
            if t is None:
                continue
            stored = normals[j] if j < len(normals) else None
            hit_n = _unit_normal(stored, tris[j])
            if _dot(n, hit_n) > -0.2:
                continue
            if best is None or t < best:
                best = t
        if best is not None and best > 1e-3:
            hits.append((area, best))
    return hits, len(ranked)


def thickness_audit(
    tris: Sequence[Tri],
    normals: Sequence[Vec3],
    min_wall_mm: float,
    min_feature_mm: float,
    thin_wall_area_frac: float = THIN_WALL_AREA_FRAC,
    tess_slack_mm: float = TESS_SLACK_MM,
) -> Tuple[List[str], List[str], List[str]]:
    """HARD/WARN/INFO for sampled wall thickness vs spec minima."""
    hard: List[str] = []
    warn: List[str] = []
    info: List[str] = []
    if not tris:
        return hard, warn, info

    hits, n_cand = sample_thickness(tris, normals)
    if not hits:
        info.append(
            f"thickness samples=0 candidates={n_cand} "
            f"(no opposing-face hits; sampled, not exact-kernel)"
        )
        return hard, warn, info

    total = sum(area for area, _ in hits)
    wall_cut = max(0.0, float(min_wall_mm) - tess_slack_mm)
    feature_cut = max(0.0, float(min_feature_mm) - tess_slack_mm)
    thin_area = sum(area for area, t in hits if t < wall_cut)
    feature_area = sum(area for area, t in hits if t < feature_cut)
    thin_frac = thin_area / total
    feature_frac = feature_area / total
    min_t = min(t for _, t in hits)
    info.append(
        f"thickness samples={len(hits)} min={min_t:.3f} mm "
        f"thin_frac={thin_frac:.3f} wall_cut={wall_cut:.3f} mm "
        f"thin_wall_area_frac={thin_wall_area_frac} tess_slack_mm={tess_slack_mm} "
        f"(sampled, not exact-kernel)"
    )
    if thin_frac > thin_wall_area_frac:
        hard.append(
            f"G-thickness: {thin_frac * 100:.1f}% of sampled area is below "
            f"geometry.min_wall_mm {min_wall_mm:.2f} mm (cut {wall_cut:.2f} mm, "
            f"limit thin_wall_area_frac={thin_wall_area_frac}); "
            f"min sample {min_t:.3f} mm"
        )
    elif feature_frac > thin_wall_area_frac * 0.5:
        warn.append(
            f"G-thickness: {feature_frac * 100:.1f}% of sampled area is near "
            f"geometry.min_feature_mm {min_feature_mm:.2f} mm "
            f"(min sample {min_t:.3f} mm)"
        )
    return hard, warn, info
