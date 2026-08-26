"""Occupancy between edge-connected shells."""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from stl_io import Tri

AABB = Tuple[float, float, float, float, float, float]


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _points_aabb(pts: Sequence) -> AABB:
    xs, ys, zs = zip(*pts)
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def _aabb_overlap(a: AABB, b: AABB, eps: float = 1e-7) -> bool:
    return (
        a[3] > b[0] + eps and b[3] > a[0] + eps
        and a[4] > b[1] + eps and b[4] > a[1] + eps
        and a[5] > b[2] + eps and b[5] > a[2] + eps
    )


def _aabb_strictly_inside(inner: AABB, outer: AABB, eps: float = 1e-7) -> bool:
    return (
        inner[0] >= outer[0] + eps and inner[3] <= outer[3] - eps
        and inner[1] >= outer[1] + eps and inner[4] <= outer[4] - eps
        and inner[2] >= outer[2] + eps and inner[5] <= outer[5] - eps
    )


def _project2(p, drop: int):
    if drop == 0:
        return (p[1], p[2])
    if drop == 1:
        return (p[0], p[2])
    return (p[0], p[1])


def _orient2(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _point_in_tri2(p, a, b, c, eps: float = 1e-9) -> bool:
    o1, o2, o3 = _orient2(a, b, p), _orient2(b, c, p), _orient2(c, a, p)
    has_neg = o1 < -eps or o2 < -eps or o3 < -eps
    has_pos = o1 > eps or o2 > eps or o3 > eps
    return not (has_neg and has_pos)


def _seg_intersect2(p, q, r, s, eps: float = 1e-9) -> bool:
    o1, o2 = _orient2(p, q, r), _orient2(p, q, s)
    o3, o4 = _orient2(r, s, p), _orient2(r, s, q)
    if (o1 > eps and o2 > eps) or (o1 < -eps and o2 < -eps):
        return False
    if (o3 > eps and o4 > eps) or (o3 < -eps and o4 < -eps):
        return False
    return True


def _coplanar_tri_intersect(normal, t1, t2) -> bool:
    drop = 0
    if abs(normal[1]) > abs(normal[drop]):
        drop = 1
    if abs(normal[2]) > abs(normal[drop]):
        drop = 2
    a = [_project2(p, drop) for p in t1]
    b = [_project2(p, drop) for p in t2]
    if any(_point_in_tri2(p, b[0], b[1], b[2]) for p in a):
        return True
    if any(_point_in_tri2(p, a[0], a[1], a[2]) for p in b):
        return True
    edges_a = ((a[0], a[1]), (a[1], a[2]), (a[2], a[0]))
    edges_b = ((b[0], b[1]), (b[1], b[2]), (b[2], b[0]))
    return any(_seg_intersect2(p, q, r, s) for p, q in edges_a for r, s in edges_b)


def _plane_isect_interval(verts, dists, axis):
    points = []
    for i in range(3):
        j = (i + 1) % 3
        di, dj = dists[i], dists[j]
        if di == 0.0:
            points.append(_dot(verts[i], axis))
        if di * dj < 0.0:
            t = di / (di - dj)
            p = (
                verts[i][0] + t * (verts[j][0] - verts[i][0]),
                verts[i][1] + t * (verts[j][1] - verts[i][1]),
                verts[i][2] + t * (verts[j][2] - verts[i][2]),
            )
            points.append(_dot(p, axis))
    if len(points) < 2:
        return None
    return (min(points), max(points))


def triangles_intersect(t1, t2, eps: float = 1e-8) -> bool:
    v0, v1, v2 = t1
    u0, u1, u2 = t2
    n1 = _cross(_sub(v1, v0), _sub(v2, v0))
    n2 = _cross(_sub(u1, u0), _sub(u2, u0))
    if _dot(n1, n1) < eps * eps or _dot(n2, n2) < eps * eps:
        return False
    d1 = -_dot(n1, v0)
    du = [0.0 if abs(x) < eps else x for x in (_dot(n1, u0) + d1, _dot(n1, u1) + d1, _dot(n1, u2) + d1)]
    if du[0] * du[1] > 0 and du[0] * du[2] > 0:
        return False
    d2 = -_dot(n2, u0)
    dv = [0.0 if abs(x) < eps else x for x in (_dot(n2, v0) + d2, _dot(n2, v1) + d2, _dot(n2, v2) + d2)]
    if dv[0] * dv[1] > 0 and dv[0] * dv[2] > 0:
        return False
    if all(x == 0.0 for x in du) or all(x == 0.0 for x in dv):
        return _coplanar_tri_intersect(n1, t1, t2)
    axis = _cross(n1, n2)
    if _dot(axis, axis) < eps * eps:
        return _coplanar_tri_intersect(n1, t1, t2)
    a = _plane_isect_interval(t1, dv, axis)
    b = _plane_isect_interval(t2, du, axis)
    if a is None or b is None:
        return False
    return not (a[1] < b[0] - eps or b[1] < a[0] - eps)


def count_overlapping_shell_pairs(
    tris: List[Tri], tri_cid: Dict[int, int], n_components: int
) -> int:
    """Crossing surfaces fail. Overlapping AABBs fail unless one shell is a cavity."""
    if n_components < 2:
        return 0
    groups: List[List[int]] = [[] for _ in range(n_components)]
    for idx, cid in tri_cid.items():
        groups[cid].append(idx)
    aabbs = [_points_aabb([p for i in group for p in tris[i]]) for group in groups]
    pairs = 0
    for i in range(n_components):
        for j in range(i + 1, n_components):
            if not _aabb_overlap(aabbs[i], aabbs[j]):
                continue
            hit = False
            for ia in groups[i]:
                if hit:
                    break
                ta = tris[ia]
                aa = _points_aabb(ta)
                for ib in groups[j]:
                    tb = tris[ib]
                    if not _aabb_overlap(aa, _points_aabb(tb)):
                        continue
                    if triangles_intersect(ta, tb):
                        hit = True
                        break
            contained = _aabb_strictly_inside(aabbs[i], aabbs[j]) or _aabb_strictly_inside(
                aabbs[j], aabbs[i]
            )
            if hit or not contained:
                pairs += 1
    return pairs
