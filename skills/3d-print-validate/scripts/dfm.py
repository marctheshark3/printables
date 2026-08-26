"""Print-orientation DFM heuristics: overhang, tessellation, open-under."""
from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from stl_io import Tri, Vec3, tri_area, tri_normal

OPEN_FRAME = {"equipment-open-frame", "equipment_open_frame", "open-frame"}


def print_up(orientation: Optional[str], axis: Optional[str]) -> Vec3:
    if axis:
        return {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}[axis.upper()]
    text = (orientation or "Z-up").upper().replace("_", "-")
    if "X" in text and "UP" in text:
        return (1.0, 0.0, 0.0)
    if "Y" in text and "UP" in text:
        return (0.0, 1.0, 0.0)
    return (0.0, 0.0, 1.0)


def overhang_fraction(
    tris: Sequence[Tri],
    normals: Sequence[Vec3],
    up: Vec3,
    max_deg: float,
    bed_support_mm: float,
) -> Tuple[float, float, float]:
    """Return (unsupported_frac, threshold, bed_excl_frac)."""
    thr = -math.sin(math.radians(max_deg))
    bed = min(p[0] * up[0] + p[1] * up[1] + p[2] * up[2] for tri in tris for p in tri)
    bad_area = 0.0
    tot_area = 0.0
    bed_excl = 0.0
    for i, (a, b, c) in enumerate(tris):
        area = tri_area(a, b, c)
        tot_area += area
        cz = (
            (a[0] + b[0] + c[0]) / 3.0 * up[0]
            + (a[1] + b[1] + c[1]) / 3.0 * up[1]
            + (a[2] + b[2] + c[2]) / 3.0 * up[2]
        )
        if cz <= bed + bed_support_mm:
            bed_excl += area
            continue
        n = normals[i] if i < len(normals) else tri_normal(a, b, c)
        if abs(n[0]) + abs(n[1]) + abs(n[2]) < 1e-9:
            n = tri_normal(a, b, c)
        nz = n[0] * up[0] + n[1] * up[1] + n[2] * up[2]
        if nz < thr:
            bad_area += area
    denom = max(tot_area - bed_excl, 1e-9)
    return bad_area / denom, thr, bed_excl / max(tot_area, 1e-9)


def tessellation_thin_frac(tris: Sequence[Tri], ntri: int, thin_edge_mm: float) -> Tuple[float, int]:
    edge_lens: List[float] = []
    step = max(1, ntri // 80000)
    for i in range(0, ntri, step):
        a, b, c = tris[i]
        for p, q in ((a, b), (b, c), (c, a)):
            d = math.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2)
            if d > 1e-6:
                edge_lens.append(d)
    if not edge_lens:
        return 0.0, 0
    thin = sum(1 for length in edge_lens if length < thin_edge_mm)
    return thin / len(edge_lens), len(edge_lens)


def open_under_fill_frac(
    tris: Sequence[Tri],
    mn: Sequence[float],
    dx: float,
    dy: float,
    dz: float,
) -> Tuple[float, float, float]:
    """Interior mid-height solid fraction for open-frame seating decks."""
    z0 = mn[2]
    under_lo = z0 + 0.30 * dz
    under_hi = z0 + 0.82 * dz
    nxg, nyg = 28, 28
    cells = [[0 for _ in range(nyg)] for _ in range(nxg)]
    cell_w = max(dx, 1e-6) / nxg
    cell_h = max(dy, 1e-6) / nyg

    def z_at_xy(px: float, py: float, a, b, c) -> Optional[float]:
        x1, y1, z1 = a
        x2, y2, z2 = b
        x3, y3, z3 = c
        den = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(den) < 1e-12:
            return None
        w1 = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / den
        w2 = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / den
        w3 = 1.0 - w1 - w2
        if w1 < -1e-6 or w2 < -1e-6 or w3 < -1e-6:
            return None
        return w1 * z1 + w2 * z2 + w3 * z3

    for a, b, c in tris:
        xs = [a[0], b[0], c[0]]
        ys = [a[1], b[1], c[1]]
        ix0 = max(0, int((min(xs) - mn[0]) / max(dx, 1e-6) * nxg) - 1)
        ix1 = min(nxg - 1, int((max(xs) - mn[0]) / max(dx, 1e-6) * nxg) + 1)
        iy0 = max(0, int((min(ys) - mn[1]) / max(dy, 1e-6) * nyg) - 1)
        iy1 = min(nyg - 1, int((max(ys) - mn[1]) / max(dy, 1e-6) * nyg) + 1)
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                z = z_at_xy(mn[0] + (ix + 0.5) * cell_w, mn[1] + (iy + 0.5) * cell_h, a, b, c)
                if z is not None and under_lo <= z <= under_hi:
                    cells[ix][iy] += 1

    margin = 3
    interior = 0
    filled = 0
    for ix in range(margin, nxg - margin):
        for iy in range(margin, nyg - margin):
            interior += 1
            if cells[ix][iy] > 0:
                filled += 1
    frac = (filled / float(interior)) if interior else 0.0
    return frac, under_lo, under_hi
