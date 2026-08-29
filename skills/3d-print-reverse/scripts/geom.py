"""Stdlib 3D helpers for reverse reconstruction. No numpy."""
from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

Vec3 = Tuple[float, float, float]
Vec2 = Tuple[float, float]
Mat3 = List[List[float]]
Tri = Tuple[Vec3, Vec3, Vec3]

EPS = 1e-12


def vadd(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vsub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vscale(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def vdot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vlen(a: Vec3) -> float:
    return math.sqrt(vdot(a, a))


def vdist(a: Vec3, b: Vec3) -> float:
    return vlen(vsub(a, b))


def vnorm(a: Vec3) -> Vec3:
    length = vlen(a)
    if length < EPS:
        return (0.0, 0.0, 1.0)
    return vscale(a, 1.0 / length)


def vmean(points: Sequence[Vec3]) -> Vec3:
    if not points:
        return (0.0, 0.0, 0.0)
    n = float(len(points))
    return (
        sum(p[0] for p in points) / n,
        sum(p[1] for p in points) / n,
        sum(p[2] for p in points) / n,
    )


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def angle_deg(a: Vec3, b: Vec3) -> float:
    return math.degrees(math.acos(clamp(vdot(vnorm(a), vnorm(b)), -1.0, 1.0)))


def tri_area(a: Vec3, b: Vec3, c: Vec3) -> float:
    return 0.5 * vlen(vcross(vsub(b, a), vsub(c, a)))


def tri_normal(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    return vnorm(vcross(vsub(b, a), vsub(c, a)))


def matvec(m: Mat3, v: Vec3) -> Vec3:
    return (
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    )


def matT(m: Mat3) -> Mat3:
    return [[m[0][0], m[1][0], m[2][0]], [m[0][1], m[1][1], m[2][1]], [m[0][2], m[1][2], m[2][2]]]


def identity3() -> Mat3:
    return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


def det3(m: Mat3) -> float:
    return (
        m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
        - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
    )


def rpy_deg_from_matrix(r: Mat3) -> Vec3:
    """ZYX intrinsic yaw-pitch-roll in degrees from a rotation matrix."""
    sy = -r[2][0]
    cy = math.sqrt(max(0.0, 1.0 - sy * sy))
    if cy < 1e-8:
        yaw = math.atan2(-r[0][1], r[1][1])
        pitch = math.asin(clamp(sy, -1.0, 1.0))
        roll = 0.0
    else:
        yaw = math.atan2(r[1][0], r[0][0])
        pitch = math.atan2(sy, cy)
        roll = math.atan2(r[2][1], r[2][2])
    return (math.degrees(roll), math.degrees(pitch), math.degrees(yaw))


def matrix_from_rpy_deg(rpy: Sequence[float]) -> Mat3:
    roll, pitch, yaw = (math.radians(float(x)) for x in rpy)
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    # R = Rz(yaw) * Ry(pitch) * Rx(roll)
    return [
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp, cp * sr, cp * cr],
    ]


def jacobi_eigen3(cov: Mat3, niter: int = 40) -> Tuple[Vec3, Mat3]:
    """Symmetric 3x3 eigen-decomposition. Returns (eigenvalues, columns=eigenvectors)."""
    a = [row[:] for row in cov]
    v = identity3()
    for _ in range(niter):
        p, q = 0, 1
        best = abs(a[0][1])
        for i, j in ((0, 2), (1, 2)):
            if abs(a[i][j]) > best:
                best = abs(a[i][j])
                p, q = i, j
        if best < 1e-15:
            break
        app, aqq, apq = a[p][p], a[q][q], a[p][q]
        tau = (aqq - app) / (2.0 * apq)
        t = math.copysign(1.0, tau) / (abs(tau) + math.sqrt(1.0 + tau * tau))
        c = 1.0 / math.sqrt(1.0 + t * t)
        s = t * c
        for k in range(3):
            if k == p or k == q:
                continue
            akp, akq = a[k][p], a[k][q]
            a[k][p] = a[p][k] = c * akp - s * akq
            a[k][q] = a[q][k] = s * akp + c * akq
        a[p][p] = app - t * apq
        a[q][q] = aqq + t * apq
        a[p][q] = a[q][p] = 0.0
        for k in range(3):
            vkp, vkq = v[k][p], v[k][q]
            v[k][p] = c * vkp - s * vkq
            v[k][q] = s * vkp + c * vkq
    evals = (a[0][0], a[1][1], a[2][2])
    return evals, v


def covariance3(points: Sequence[Vec3], center: Vec3 | None = None) -> Mat3:
    if not points:
        return [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    c = center if center is not None else vmean(points)
    acc = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    inv = 1.0 / float(len(points))
    for p in points:
        d = vsub(p, c)
        for i in range(3):
            for j in range(3):
                acc[i][j] += d[i] * d[j] * inv
    return acc


def orthonormalize(axes: Sequence[Vec3]) -> Mat3:
    x = vnorm(axes[0])
    y = vsub(axes[1], vscale(x, vdot(axes[1], x)))
    if vlen(y) < 1e-9:
        helper = (0.0, 0.0, 1.0) if abs(x[2]) < 0.9 else (0.0, 1.0, 0.0)
        y = vsub(helper, vscale(x, vdot(helper, x)))
    y = vnorm(y)
    z = vcross(x, y)
    if vlen(z) < 1e-9:
        z = (0.0, 0.0, 1.0)
    else:
        z = vnorm(z)
    y = vcross(z, x)
    m = [list(x), list(y), list(z)]
    if det3(m) < 0:
        m[2] = [-m[2][0], -m[2][1], -m[2][2]]
    return m


def snap_axes_to_xyz(evecs: Mat3) -> Mat3:
    """Permute/flip eigenvectors so they snap to a right-handed XYZ frame."""
    cols = [(evecs[0][i], evecs[1][i], evecs[2][i]) for i in range(3)]
    assigned: list[Vec3 | None] = [None, None, None]
    used = set()
    for col in cols:
        world = max(range(3), key=lambda i: abs(col[i]) if i not in used else -1.0)
        used.add(world)
        axis = col if col[world] >= 0 else vscale(col, -1.0)
        assigned[world] = axis
    for i, axis in enumerate(assigned):
        if axis is None:
            assigned[i] = (1.0 if i == 0 else 0.0, 1.0 if i == 1 else 0.0, 1.0 if i == 2 else 0.0)
    return orthonormalize([assigned[0], assigned[1], assigned[2]])  # type: ignore[arg-type]


def world_aligned_area_frac(normals_areas: Iterable[Tuple[Vec3, float]], thresh_deg: float = 8.0) -> float:
    cos_t = math.cos(math.radians(thresh_deg))
    total = 0.0
    aligned = 0.0
    for n, area in normals_areas:
        total += area
        if max(abs(n[0]), abs(n[1]), abs(n[2])) >= cos_t:
            aligned += area
    if total <= EPS:
        return 1.0
    return aligned / total


def point_plane_signed(p: Vec3, origin: Vec3, normal: Vec3) -> float:
    return vdot(vsub(p, origin), normal)


def fit_plane(points: Sequence[Vec3], normals: Sequence[Vec3] | None = None) -> dict | None:
    if len(points) < 3:
        return None
    origin = vmean(points)
    if normals:
        n = vnorm(vmean([vnorm(x) for x in normals]))
    else:
        cov = covariance3(points, origin)
        evals, evecs = jacobi_eigen3(cov)
        idx = min(range(3), key=lambda i: evals[i])
        n = vnorm((evecs[0][idx], evecs[1][idx], evecs[2][idx]))
    if normals and vdot(n, vmean(normals)) < 0:
        n = vscale(n, -1.0)
    max_dev = 0.0
    for p in points:
        max_dev = max(max_dev, abs(point_plane_signed(p, origin, n)))
    return {"kind": "plane", "origin": origin, "normal": n, "max_dev": max_dev}


def point_axis_distance(p: Vec3, origin: Vec3, axis: Vec3) -> float:
    return vlen(vcross(vsub(p, origin), axis))


def _solve3(a: Mat3, b: Vec3) -> Vec3 | None:
    d = det3(a)
    if abs(d) < 1e-18:
        return None
    def col(m, i, vec):
        out = [row[:] for row in m]
        for r in range(3):
            out[r][i] = vec[r]
        return out
    return (det3(col(a, 0, b)) / d, det3(col(a, 1, b)) / d, det3(col(a, 2, b)) / d)


def fit_circle_2d(pts: Sequence[Vec2]) -> tuple[Vec2, float] | None:
    if len(pts) < 3:
        return None
    sxx = sxy = syy = sx = sy = sxz = syz = 0.0
    n = float(len(pts))
    for x, y in pts:
        r2 = x * x + y * y
        sxx += x * x
        syy += y * y
        sxy += x * y
        sx += x
        sy += y
        sxz += x * r2
        syz += y * r2
    # 2a x + 2b y + c = x^2+y^2, a,b = center
    a = [[2 * sxx, 2 * sxy, sx], [2 * sxy, 2 * syy, sy], [sx, sy, n]]
    rhs = (sxz, syz, sum(x * x + y * y for x, y in pts))
    sol = _solve3(a, rhs)
    if sol is None:
        return None
    cx, cy, c = sol
    r2 = c + cx * cx + cy * cy
    if r2 <= EPS:
        return None
    return (cx, cy), math.sqrt(r2)


def fit_cylinder(points: Sequence[Vec3], normals: Sequence[Vec3] | None = None) -> dict | None:
    if len(points) < 6:
        return None
    origin = vmean(points)
    if normals:
        nn = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        for n in normals:
            u = vnorm(n)
            for i in range(3):
                for j in range(3):
                    nn[i][j] += u[i] * u[j]
        evals, evecs = jacobi_eigen3(nn)
        idx = min(range(3), key=lambda i: evals[i])
        axis = vnorm((evecs[0][idx], evecs[1][idx], evecs[2][idx]))
    else:
        cov = covariance3(points, origin)
        evals, evecs = jacobi_eigen3(cov)
        idx = max(range(3), key=lambda i: evals[i])
        axis = vnorm((evecs[0][idx], evecs[1][idx], evecs[2][idx]))
    x_axis, y_axis = plane_basis(axis)
    pts2 = [project_to_plane(p, origin, axis, x_axis, y_axis) for p in points]
    circ = fit_circle_2d(pts2)
    if circ is None:
        return None
    (cu, cv), radius = circ
    if radius < EPS:
        return None
    center = vadd(origin, vadd(vscale(x_axis, cu), vscale(y_axis, cv)))
    max_dev = 0.0
    for p in points:
        max_dev = max(max_dev, abs(point_axis_distance(p, center, axis) - radius))
    axial = [vdot(vsub(p, center), axis) for p in points]
    height = max(axial) - min(axial) if axial else 0.0
    return {
        "kind": "cylinder",
        "origin": center,
        "axis": axis,
        "radius": radius,
        "height": height,
        "max_dev": max_dev,
    }


def fit_sphere(points: Sequence[Vec3]) -> dict | None:
    if len(points) < 4:
        return None
    center = vmean(points)
    radii = [vdist(p, center) for p in points]
    radius = sum(radii) / float(len(radii))
    if radius < EPS:
        return None
    max_dev = max(abs(r - radius) for r in radii)
    return {"kind": "sphere", "origin": center, "radius": radius, "max_dev": max_dev}


def fit_cone(points: Sequence[Vec3], normals: Sequence[Vec3] | None = None) -> dict | None:
    cyl = fit_cylinder(points, normals)
    if cyl is None or len(points) < 8:
        return None
    origin, axis = cyl["origin"], cyl["axis"]
    axial = [vdot(vsub(p, origin), axis) for p in points]
    radii = [point_axis_distance(p, origin, axis) for p in points]
    t0, t1 = min(axial), max(axial)
    if t1 - t0 < EPS:
        return None
    # Linear radius vs axial: r = r0 + s * t
    n = float(len(points))
    mean_t = sum(axial) / n
    mean_r = sum(radii) / n
    var_t = sum((t - mean_t) ** 2 for t in axial)
    if var_t < EPS:
        return None
    slope = sum((t - mean_t) * (r - mean_r) for t, r in zip(axial, radii)) / var_t
    r0 = mean_r - slope * mean_t
    max_dev = 0.0
    for t, r in zip(axial, radii):
        max_dev = max(max_dev, abs(r - (r0 + slope * t)))
    if abs(slope) * (t1 - t0) < 1e-4:
        return None
    return {
        "kind": "cone",
        "origin": origin,
        "axis": axis,
        "r0": r0,
        "slope": slope,
        "max_dev": max_dev,
    }


def project_to_plane(p: Vec3, origin: Vec3, normal: Vec3, x_axis: Vec3, y_axis: Vec3) -> Vec2:
    d = vsub(p, origin)
    return (vdot(d, x_axis), vdot(d, y_axis))


def plane_basis(normal: Vec3) -> Tuple[Vec3, Vec3]:
    n = vnorm(normal)
    helper = (1.0, 0.0, 0.0) if abs(n[0]) < 0.9 else (0.0, 1.0, 0.0)
    x = vnorm(vcross(helper, n))
    y = vcross(n, x)
    return x, y


def plane_name(normal: Vec3, origin: Vec3, snap_deg: float = 8.0) -> str:
    n = vnorm(normal)
    ax = max(range(3), key=lambda i: abs(n[i]))
    if math.degrees(math.acos(clamp(abs(n[ax]), 0.0, 1.0))) > snap_deg:
        return "3-point"
    offset = origin[ax]
    if abs(offset) <= 1e-6:
        return ("yz", "xz", "xy")[ax]
    return "offset"


def closest_point_on_triangle(p: Vec3, a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    ab, ac, ap = vsub(b, a), vsub(c, a), vsub(p, a)
    d1, d2 = vdot(ab, ap), vdot(ac, ap)
    if d1 <= 0.0 and d2 <= 0.0:
        return a
    bp = vsub(p, b)
    d3, d4 = vdot(ab, bp), vdot(ac, bp)
    if d3 >= 0.0 and d4 <= d3:
        return b
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        return vadd(a, vscale(ab, v))
    cp = vsub(p, c)
    d5, d6 = vdot(ab, cp), vdot(ac, cp)
    if d6 >= 0.0 and d5 <= d6:
        return c
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        return vadd(a, vscale(ac, w))
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return vadd(b, vscale(vsub(c, b), w))
    denom = 1.0 / (va + vb + vc)
    v = vb * denom
    w = vc * denom
    return vadd(a, vadd(vscale(ab, v), vscale(ac, w)))


def snap_value(raw: float, snap_mm: float | None) -> float:
    if snap_mm is None or snap_mm <= 0:
        return raw
    return round(raw / snap_mm) * snap_mm
