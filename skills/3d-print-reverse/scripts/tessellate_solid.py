"""Tessellate prismatic IR solids without OCC (unit-CI STL path)."""
from __future__ import annotations

import math
from typing import Any, Iterable, List, Sequence, Tuple

from geom import Tri, Vec2, Vec3, vadd, vcross, vdot, vnorm, vscale, vsub

Vec2 = Tuple[float, float]


def _seg_n(n: int = 32) -> int:
    return max(8, int(n))


def discretize_entities(entities: Sequence[dict[str, Any]], segs: int = 32) -> list[Vec2]:
    pts: list[Vec2] = []
    for ent in entities:
        kind = ent.get("type")
        if kind == "circle":
            cx, cy = ent["center_mm"]
            r = float(ent["radius_mm"])
            for i in range(segs):
                a = 2.0 * math.pi * i / segs
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        elif kind == "line":
            a = tuple(ent["a_mm"])
            b = tuple(ent["b_mm"])
            if not pts or (abs(pts[-1][0] - a[0]) + abs(pts[-1][1] - a[1])) > 1e-9:
                pts.append((float(a[0]), float(a[1])))
            pts.append((float(b[0]), float(b[1])))
        elif kind == "polyline":
            for p in ent.get("points_mm") or []:
                pts.append((float(p[0]), float(p[1])))
        elif kind == "arc":
            cx, cy = ent["center_mm"]
            r = float(ent["radius_mm"])
            a0 = math.radians(float(ent.get("start_deg", 0.0)))
            a1 = math.radians(float(ent.get("end_deg", 90.0)))
            steps = max(4, segs // 4)
            for i in range(steps + 1):
                t = a0 + (a1 - a0) * i / steps
                pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    # drop closing duplicate
    if len(pts) > 1 and abs(pts[0][0] - pts[-1][0]) < 1e-9 and abs(pts[0][1] - pts[-1][1]) < 1e-9:
        pts = pts[:-1]
    return _dedupe(pts)


def _dedupe(pts: Sequence[Vec2], eps: float = 1e-9) -> list[Vec2]:
    out: list[Vec2] = []
    for p in pts:
        if not out or abs(out[-1][0] - p[0]) + abs(out[-1][1] - p[1]) > eps:
            out.append((float(p[0]), float(p[1])))
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) + abs(out[0][1] - out[-1][1]) <= eps:
        out = out[:-1]
    return out


def _area(poly: Sequence[Vec2]) -> float:
    acc = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        acc += x1 * y2 - x2 * y1
    return 0.5 * acc


def _ensure_ccw(poly: list[Vec2]) -> list[Vec2]:
    return poly if _area(poly) >= 0 else list(reversed(poly))


def _ensure_cw(poly: list[Vec2]) -> list[Vec2]:
    return poly if _area(poly) <= 0 else list(reversed(poly))


def _point_in_tri(p: Vec2, a: Vec2, b: Vec2, c: Vec2) -> bool:
    v0 = (c[0] - a[0], c[1] - a[1])
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (p[0] - a[0], p[1] - a[1])
    dot00 = v0[0] * v0[0] + v0[1] * v0[1]
    dot01 = v0[0] * v1[0] + v0[1] * v1[1]
    dot02 = v0[0] * v2[0] + v0[1] * v2[1]
    dot11 = v1[0] * v1[0] + v1[1] * v1[1]
    dot12 = v1[0] * v2[0] + v1[1] * v2[1]
    denom = dot00 * dot11 - dot01 * dot01
    if abs(denom) < 1e-18:
        return False
    u = (dot11 * dot02 - dot01 * dot12) / denom
    v = (dot00 * dot12 - dot01 * dot02) / denom
    return u >= -1e-9 and v >= -1e-9 and u + v <= 1.0 + 1e-9


def _cross(a: Vec2, b: Vec2, c: Vec2) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def earclip(poly: Sequence[Vec2]) -> list[tuple[int, int, int]]:
    n = len(poly)
    if n < 3:
        return []
    if n == 3:
        return [(0, 1, 2)]
    idx = list(range(n))
    if _area(poly) < 0:
        idx.reverse()
    tris: list[tuple[int, int, int]] = []
    guard = 0
    while len(idx) > 3 and guard < n * n:
        guard += 1
        clipped = False
        m = len(idx)
        for i in range(m):
            i0, i1, i2 = idx[(i - 1) % m], idx[i], idx[(i + 1) % m]
            a, b, c = poly[i0], poly[i1], poly[i2]
            if _cross(a, b, c) <= 1e-12:
                continue
            if any(
                _point_in_tri(poly[j], a, b, c)
                and _dist2(poly[j], a) > 1e-16
                and _dist2(poly[j], b) > 1e-16
                and _dist2(poly[j], c) > 1e-16
                for j in idx
                if j not in (i0, i1, i2)
            ):
                continue
            tris.append((i0, i1, i2))
            del idx[i]
            clipped = True
            break
        if not clipped:
            break
    if len(idx) == 3:
        tris.append((idx[0], idx[1], idx[2]))
    return tris


def _dist2(a: Vec2, b: Vec2) -> float:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _closest_on_edges(pt: Vec2, loop: Sequence[Vec2]) -> tuple[int, Vec2, float]:
    """Return (insert_after_index, point_on_edge, t)."""
    best = 1e99
    found = (0, loop[0], 0.0)
    n = len(loop)
    for i in range(n):
        a, b = loop[i], loop[(i + 1) % n]
        ab = (b[0] - a[0], b[1] - a[1])
        ab2 = ab[0] * ab[0] + ab[1] * ab[1]
        if ab2 < 1e-18:
            continue
        t = ((pt[0] - a[0]) * ab[0] + (pt[1] - a[1]) * ab[1]) / ab2
        t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
        q = (a[0] + t * ab[0], a[1] + t * ab[1])
        d = _dist2(pt, q)
        if d < best:
            best = d
            found = (i, q, t)
    return found


def merge_holes(outer: list[Vec2], holes: Sequence[list[Vec2]]) -> list[Vec2]:
    poly = list(outer)
    for hole in holes:
        h = list(hole)
        if len(h) < 3:
            continue
        j = max(range(len(h)), key=lambda k: h[k][0])
        i, q, t = _closest_on_edges(h[j], poly)
        if t > 1e-6 and t < 1.0 - 1e-6:
            poly = poly[: i + 1] + [q] + poly[i + 1 :]
            i = i + 1
        elif t >= 1.0 - 1e-6:
            i = (i + 1) % len(poly)
        poly = poly[: i + 1] + h[j:] + h[:j] + [h[j], poly[i]] + poly[i + 1 :]
    return poly


def _ray_seg(origin: Vec2, ang: float, a: Vec2, b: Vec2) -> Vec2 | None:
    dx, dy = math.cos(ang), math.sin(ang)
    sx, sy = b[0] - a[0], b[1] - a[1]
    denom = dx * sy - dy * sx
    if abs(denom) < 1e-12:
        return None
    ox, oy = origin
    t = ((a[0] - ox) * sy - (a[1] - oy) * sx) / denom
    u = ((a[0] - ox) * dy - (a[1] - oy) * dx) / denom
    if t > 1e-9 and 0.0 <= u <= 1.0:
        return (ox + t * dx, oy + t * dy)
    return None


def _ray_hit_tri(origin: Vec2, ang: float, a: Vec2, b: Vec2, c: Vec2) -> Vec2:
    hits = [h for h in (_ray_seg(origin, ang, a, b), _ray_seg(origin, ang, b, c), _ray_seg(origin, ang, c, a)) if h]
    if not hits:
        return origin
    return min(hits, key=lambda p: (p[0] - origin[0]) ** 2 + (p[1] - origin[1]) ** 2)


def _walk_closed(loop: Sequence[Vec2], i0: int, i1: int) -> list[Vec2]:
    n = len(loop)
    out = [loop[i0]]
    i = i0
    guard = 0
    while i != i1 and guard < n + 2:
        i = (i + 1) % n
        out.append(loop[i])
        guard += 1
    return out


def punch_loop_in_triangle(
    a: Vec2, b: Vec2, c: Vec2, hole: Sequence[Vec2]
) -> list[tuple[Vec2, Vec2, Vec2]]:
    """Replace triangle ABC with a sleeve to `hole`. Reuses A,B,C (no Steiner outer verts)."""
    if len(hole) < 3:
        return [(a, b, c)]
    cx = sum(p[0] for p in hole) / len(hole)
    cy = sum(p[1] for p in hole) / len(hole)
    if not _point_in_tri((cx, cy), a, b, c):
        return [(a, b, c)]
    indexed = list(hole)
    indexed.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    n = len(indexed)

    def nearest(p: Vec2) -> int:
        return min(range(n), key=lambda i: (indexed[i][0] - p[0]) ** 2 + (indexed[i][1] - p[1]) ** 2)

    corners = (a, b, c)
    ixs = [nearest(p) for p in corners]
    tris: list[tuple[Vec2, Vec2, Vec2]] = []
    for e in range(3):
        p, q = corners[e], corners[(e + 1) % 3]
        chain = _walk_closed(indexed, ixs[e], ixs[(e + 1) % 3])
        alt = list(reversed(_walk_closed(indexed, ixs[(e + 1) % 3], ixs[e])))
        if len(alt) < len(chain):
            chain = alt
        if len(chain) == 1:
            tris.append((p, q, chain[0]))
            continue
        for k in range(len(chain) - 1):
            tris.append((p, chain[k], chain[k + 1]))
        tris.append((p, chain[-1], q))
    return tris


def triangulate_profile(outer: list[Vec2], holes: Sequence[list[Vec2]]) -> list[tuple[Vec2, Vec2, Vec2]]:
    outer_c = _ensure_ccw(_dedupe(outer))
    hole_c = [_ensure_cw(_dedupe(h)) for h in holes if len(h) >= 3]
    merged = merge_holes(outer_c, hole_c)
    tris_i = earclip(merged)
    if len(tris_i) >= 3:
        return [(merged[i], merged[j], merged[k]) for i, j, k in tris_i]
    # Fallback: earclip outer, punch holes that sit in a single triangle.
    idx = earclip(outer_c)
    faces = [(outer_c[i], outer_c[j], outer_c[k]) for i, j, k in idx]
    if not hole_c:
        return faces
    out: list[tuple[Vec2, Vec2, Vec2]] = []
    used_holes: set[int] = set()
    for tri in faces:
        punched = False
        for hi, hole in enumerate(hole_c):
            if hi in used_holes:
                continue
            cx = sum(p[0] for p in hole) / len(hole)
            cy = sum(p[1] for p in hole) / len(hole)
            if _point_in_tri((cx, cy), tri[0], tri[1], tri[2]):
                out.extend(punch_loop_in_triangle(tri[0], tri[1], tri[2], hole))
                used_holes.add(hi)
                punched = True
                break
        if not punched:
            out.append(tri)
    return out


def _lift(p: Vec2, origin: Vec3, x_axis: Vec3, y_axis: Vec3, z: float, z_axis: Vec3) -> Vec3:
    return (
        origin[0] + x_axis[0] * p[0] + y_axis[0] * p[1] + z_axis[0] * z,
        origin[1] + x_axis[1] * p[0] + y_axis[1] * p[1] + z_axis[1] * z,
        origin[2] + x_axis[2] * p[0] + y_axis[2] * p[1] + z_axis[2] * z,
    )


def _orient_outward(tris: list[Tri]) -> list[Tri]:
    """Make neighbor windings consistent, then flip the shell for positive volume."""
    from collections import defaultdict, deque

    from mesh_common import weld_triangles
    from stl_io import bbox_and_volume

    if not tris:
        return tris
    verts, faces, _n = weld_triangles(tris, 1e-5)
    if not faces:
        return tris
    edge_to_faces: dict[tuple[int, int], list[int]] = defaultdict(list)
    for fi, (a, b, c) in enumerate(faces):
        for u, v in ((a, b), (b, c), (c, a)):
            edge_to_faces[(u, v) if u < v else (v, u)].append(fi)
    oriented = [list(f) for f in faces]
    seen = [False] * len(faces)
    for seed in range(len(faces)):
        if seen[seed]:
            continue
        q: deque[int] = deque([seed])
        seen[seed] = True
        while q:
            fi = q.popleft()
            a, b, c = oriented[fi]
            for u, v in ((a, b), (b, c), (c, a)):
                key = (u, v) if u < v else (v, u)
                for fj in edge_to_faces[key]:
                    if fj == fi or seen[fj]:
                        continue
                    oa, ob, oc = oriented[fj]
                    if (u, v) in ((oa, ob), (ob, oc), (oc, oa)):
                        oriented[fj] = [oa, oc, ob]
                    seen[fj] = True
                    q.append(fj)
    out = [(verts[i], verts[j], verts[k]) for i, j, k in oriented]
    _mn, _mx, vol = bbox_and_volume(out)
    if vol < 0:
        out = [(a, c, b) for a, b, c in out]
    return out


def _loops_from_tris2(tris2: Sequence[tuple[Vec2, Vec2, Vec2]]) -> list[list[Vec2]]:
    from collections import defaultdict

    def q(p: Vec2) -> tuple[int, int]:
        return (int(round(p[0] * 1e6)), int(round(p[1] * 1e6)))

    edge_count: dict[tuple[tuple[int, int], tuple[int, int]], int] = defaultdict(int)
    directed: dict[tuple[tuple[int, int], tuple[int, int]], tuple[Vec2, Vec2]] = {}
    for a, b, c in tris2:
        for u, v in ((a, b), (b, c), (c, a)):
            ku, kv = q(u), q(v)
            key = (ku, kv) if ku < kv else (kv, ku)
            edge_count[key] += 1
            directed[key] = (u, v)
    boundary = [directed[k] for k, n in edge_count.items() if n == 1]
    remaining = list(boundary)
    used = [False] * len(remaining)
    loops: list[list[Vec2]] = []
    for i in range(len(remaining)):
        if used[i]:
            continue
        u, v = remaining[i]
        used[i] = True
        loop = [u]
        cur = v
        guard = 0
        while q(cur) != q(u) and guard < len(remaining) + 2:
            loop.append(cur)
            nxt = None
            for j, (a, b) in enumerate(remaining):
                if used[j]:
                    continue
                if q(a) == q(cur):
                    nxt = b
                    used[j] = True
                    break
                if q(b) == q(cur):
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


def extrude_profile(
    outer: list[Vec2],
    holes: Sequence[list[Vec2]],
    *,
    origin: Vec3,
    x_axis: Vec3,
    y_axis: Vec3,
    z_axis: Vec3,
    depth: float,
) -> list[Tri]:
    tris2 = triangulate_profile(outer, holes)
    z_axis = vnorm(z_axis)
    x_axis = vnorm(x_axis)
    y_axis = vnorm(y_axis)
    top: list[Tri] = []
    bot: list[Tri] = []
    for a, b, c in tris2:
        pa = _lift(a, origin, x_axis, y_axis, depth, z_axis)
        pb = _lift(b, origin, x_axis, y_axis, depth, z_axis)
        pc = _lift(c, origin, x_axis, y_axis, depth, z_axis)
        qa = _lift(a, origin, x_axis, y_axis, 0.0, z_axis)
        qb = _lift(b, origin, x_axis, y_axis, 0.0, z_axis)
        qc = _lift(c, origin, x_axis, y_axis, 0.0, z_axis)
        top.append((pa, pb, pc))
        bot.append((qa, qc, qb))
    walls: list[Tri] = []
    loops = _loops_from_tris2(tris2)
    if not loops:
        loops = [_ensure_ccw(outer)] + [_ensure_cw(h) for h in holes if len(h) >= 3]

    def wall_loop(loop: Sequence[Vec2], inward: bool) -> None:
        n = len(loop)
        for i in range(n):
            p0, p1 = loop[i], loop[(i + 1) % n]
            a = _lift(p0, origin, x_axis, y_axis, 0.0, z_axis)
            b = _lift(p1, origin, x_axis, y_axis, 0.0, z_axis)
            c = _lift(p1, origin, x_axis, y_axis, depth, z_axis)
            d = _lift(p0, origin, x_axis, y_axis, depth, z_axis)
            invert = inward
            if invert:
                walls.append((a, d, c))
                walls.append((a, c, b))
            else:
                walls.append((a, b, c))
                walls.append((a, c, d))

    # Largest loop is outer; others are holes.
    loops_sorted = sorted(loops, key=lambda lp: abs(_area(lp)), reverse=True)
    for i, loop in enumerate(loops_sorted):
        wall_loop(loop, inward=i > 0)
    return _orient_outward(top + bot + walls)


def _box_tris(xmin, ymin, zmin, xmax, ymax, zmax) -> list[Tri]:
    p = [
        (xmin, ymin, zmin),
        (xmax, ymin, zmin),
        (xmax, ymax, zmin),
        (xmin, ymax, zmin),
        (xmin, ymin, zmax),
        (xmax, ymin, zmax),
        (xmax, ymax, zmax),
        (xmin, ymax, zmax),
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


def _looks_rectangle(pts: Sequence[Vec2], eps: float = 1e-3) -> bool:
    if len(pts) != 4:
        return False
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (max(xs) - min(xs) > eps) and (max(ys) - min(ys) > eps)


def aabb_param_for_axis(axis: Sequence[float]) -> str:
    """Map a unit axis onto PRINT_SPEC AABB names (X=width, Y=depth, Z=height)."""
    ax = max(range(3), key=lambda i: abs(float(axis[i])))
    return ("width_mm", "depth_mm", "height_mm")[ax]


def dim_value(ir: dict[str, Any], parameter: str, default: float | None = None) -> float:
    for d in ir.get("dimensions") or []:
        if d.get("parameter") == parameter:
            return float(d["value_mm"])
    if default is None:
        raise KeyError(parameter)
    return default


def tessellate_ir(ir: dict[str, Any], *, segs: int = 32) -> list[Tri]:
    sketches = {s["id"]: s for s in ir.get("sketches") or []}
    features = ir.get("features") or []
    extrudes = [f for f in features if f.get("type") == "extrude" and f.get("op") == "add"]
    holes = [f for f in features if f.get("type") == "hole"]
    if not extrudes:
        # AABB box fallback for tests that only have dimensions.
        w = dim_value(ir, "width_mm", 0.0)
        d = dim_value(ir, "depth_mm", 0.0)
        h = dim_value(ir, "height_mm", 0.0)
        if min(w, d, h) <= 0:
            return []
        hx, hy, hz = w / 2.0, d / 2.0, h / 2.0
        return _box_tris(-hx, -hy, -hz, hx, hy, hz)

    feat = extrudes[0]
    sketch = sketches.get(feat.get("sketch"))
    depth = float(feat.get("depth_mm") or dim_value(ir, "extrude_depth_mm", 0.0))
    if sketch is None:
        w = dim_value(ir, "width_mm")
        dpth = dim_value(ir, "depth_mm")
        hx, hy, hz = w / 2.0, dpth / 2.0, depth / 2.0
        return _box_tris(-hx, -hy, -hz, hx, hy, hz)

    origin = tuple(float(x) for x in sketch["origin_mm"])  # type: ignore[misc]
    x_axis = tuple(float(x) for x in sketch["x_axis"])  # type: ignore[misc]
    y_axis = tuple(float(x) for x in sketch["y_axis"])  # type: ignore[misc]
    z_axis = tuple(float(x) for x in (feat.get("direction") or sketch.get("normal")))  # type: ignore[misc]
    outer = []
    hole_loops: list[list[Vec2]] = []
    for prof in sketch.get("profiles") or []:
        pts = discretize_entities(prof.get("entities") or [], segs=segs)
        if prof.get("role") == "hole" or str(prof.get("id", "")).startswith("hole"):
            hole_loops.append(pts)
        elif not outer:
            outer = pts
        else:
            hole_loops.append(pts)
    if not outer:
        return []
    # Rectangular sketch: honor named AABB parameters in the sketch UV frame
    # (width=X, depth=Y, height=Z). Do not paste width×depth onto (u,v) when
    # x_axis is not world X — that swaps the speaker 35×25 box by 5 mm.
    if _looks_rectangle(outer):
        try:
            hu = dim_value(ir, aabb_param_for_axis(x_axis)) / 2.0
            hv = dim_value(ir, aabb_param_for_axis(y_axis)) / 2.0
        except KeyError:
            hu = hv = 0.0
        if hu > 0.0 and hv > 0.0:
            cx = sum(p[0] for p in outer) / len(outer)
            cy = sum(p[1] for p in outer) / len(outer)
            outer = [
                (cx - hu, cy - hv),
                (cx + hu, cy - hv),
                (cx + hu, cy + hv),
                (cx - hu, cy + hv),
            ]
    sketch_has_holes = any(
        (p.get("role") == "hole") or str(p.get("id", "")).startswith("hole")
        for p in (sketch.get("profiles") or [])
    )
    # Add IR holes that are circles not already in the sketch.
    for hole in holes:
        if sketch_has_holes:
            break
        if hole.get("origin_mm") and hole.get("diameter_mm"):
            ox, oy, _oz = hole["origin_mm"]
            # project hole origin onto sketch
            r = float(hole["diameter_mm"]) / 2.0
            already = False
            for loop in hole_loops:
                if loop and abs(math.hypot(loop[0][0] - ox, loop[0][1] - oy) - r) < 0.5:
                    already = True
            # origin_mm is 3D; project
            from geom import project_to_plane, vsub

            rel = vsub(tuple(hole["origin_mm"]), origin)  # type: ignore[arg-type]
            cx = vdot(rel, x_axis)
            cy = vdot(rel, y_axis)
            if not already:
                circ = []
                for i in range(segs):
                    a = 2.0 * math.pi * i / segs
                    circ.append((cx + r * math.cos(a), cy + r * math.sin(a)))
                hole_loops.append(circ)
    return extrude_profile(
        outer,
        hole_loops,
        origin=origin,  # type: ignore[arg-type]
        x_axis=x_axis,  # type: ignore[arg-type]
        y_axis=y_axis,  # type: ignore[arg-type]
        z_axis=z_axis,  # type: ignore[arg-type]
        depth=depth,
    )
