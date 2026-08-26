"""STL load and basic mesh measures. Stdlib only."""
from __future__ import annotations

import math
import struct
from pathlib import Path
from typing import List, Tuple

Vec3 = Tuple[float, float, float]
Tri = Tuple[Vec3, Vec3, Vec3]


def load_binary_stl(path: Path) -> Tuple[List[Vec3], List[Tri], int]:
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError("STL too small")
    n = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + n * 50
    if n <= 0 or n > 50_000_000 or expected > len(data) + 50:
        if data[:5].lower() == b"solid" and b"facet" in data[:2000].lower():
            return load_ascii_stl(data.decode("utf-8", errors="replace"))
        raise ValueError(f"Not a binary STL or triangle count absurd: n={n}")

    tris: List[Tri] = []
    normals: List[Vec3] = []
    off = 84
    for _ in range(n):
        nx, ny, nz, x1, y1, z1, x2, y2, z2, x3, y3, z3 = struct.unpack_from("<12f", data, off)
        off += 50
        normals.append((nx, ny, nz))
        tris.append(((x1, y1, z1), (x2, y2, z2), (x3, y3, z3)))
    return normals, tris, n


def load_ascii_stl(text: str) -> Tuple[List[Vec3], List[Tri], int]:
    normals: List[Vec3] = []
    tris: List[Tri] = []
    cur_n: Vec3 = (0.0, 0.0, 1.0)
    verts: List[Vec3] = []
    for line in text.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        if parts[0] == "facet" and len(parts) >= 5 and parts[1] == "normal":
            cur_n = (float(parts[2]), float(parts[3]), float(parts[4]))
            verts = []
        elif parts[0] == "vertex" and len(parts) >= 4:
            verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif parts[0] == "endfacet" and len(verts) >= 3:
            normals.append(cur_n)
            tris.append((verts[0], verts[1], verts[2]))
    return normals, tris, len(tris)


def tri_area(a: Vec3, b: Vec3, c: Vec3) -> float:
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cx = ab[1] * ac[2] - ab[2] * ac[1]
    cy = ab[2] * ac[0] - ab[0] * ac[2]
    cz = ab[0] * ac[1] - ab[1] * ac[0]
    return 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)


def tri_normal(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    nx = ab[1] * ac[2] - ab[2] * ac[1]
    ny = ab[2] * ac[0] - ab[0] * ac[2]
    nz = ab[0] * ac[1] - ab[1] * ac[0]
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / length, ny / length, nz / length)


def bbox_and_volume(tris: List[Tri]) -> Tuple[List[float], List[float], float]:
    mn = [1e30, 1e30, 1e30]
    mx = [-1e30, -1e30, -1e30]
    vol = 0.0
    for a, b, c in tris:
        for p in (a, b, c):
            for i in range(3):
                if p[i] < mn[i]:
                    mn[i] = p[i]
                if p[i] > mx[i]:
                    mx[i] = p[i]
        x1, y1, z1 = a
        x2, y2, z2 = b
        x3, y3, z3 = c
        vol += (
            x1 * (y2 * z3 - y3 * z2)
            - y1 * (x2 * z3 - x3 * z2)
            + z1 * (x2 * y3 - x3 * y2)
        ) / 6.0
    return mn, mx, vol
