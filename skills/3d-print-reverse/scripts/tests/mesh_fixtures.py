"""Independent triangle fixtures for reverse tests."""
from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

Vec3 = Tuple[float, float, float]
Tri = Tuple[Vec3, Vec3, Vec3]


def cube_tris(size: float = 20.0, origin: Vec3 = (0.0, 0.0, 0.0)) -> List[Tri]:
    x0, y0, z0 = origin
    p = [
        (x0, y0, z0),
        (x0 + size, y0, z0),
        (x0 + size, y0 + size, z0),
        (x0, y0 + size, z0),
        (x0, y0, z0 + size),
        (x0 + size, y0, z0 + size),
        (x0 + size, y0 + size, z0 + size),
        (x0, y0 + size, z0 + size),
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


def plate_with_hole_tris(
    length: float = 30.0,
    thick: float = 4.0,
    radius: float = 5.0,
    segs: int = 32,
) -> List[Tri]:
    """Closed square plate in XY with a cylindrical hole through Z at the origin."""
    h = length / 2.0
    z0, z1 = -thick / 2.0, thick / 2.0

    def square_at_angle(ang: float) -> Tuple[float, float]:
        c, s = math.cos(ang), math.sin(ang)
        tx = h / abs(c) if abs(c) > 1e-12 else 1e99
        ty = h / abs(s) if abs(s) > 1e-12 else 1e99
        t = min(tx, ty)
        return (t * c, t * s)

    outer = [square_at_angle(2.0 * math.pi * i / segs) for i in range(segs)]
    inner = [
        (radius * math.cos(2.0 * math.pi * i / segs), radius * math.sin(2.0 * math.pi * i / segs))
        for i in range(segs)
    ]
    tris: List[Tri] = []

    def lift(p, z):
        return (p[0], p[1], z)

    for i in range(segs):
        i2 = (i + 1) % segs
        o0, o1, n0, n1 = outer[i], outer[i2], inner[i], inner[i2]
        # top
        tris.append((lift(o0, z1), lift(o1, z1), lift(n1, z1)))
        tris.append((lift(o0, z1), lift(n1, z1), lift(n0, z1)))
        # bottom
        tris.append((lift(o0, z0), lift(n1, z0), lift(o1, z0)))
        tris.append((lift(o0, z0), lift(n0, z0), lift(n1, z0)))
        # outer wall
        tris.append((lift(o0, z0), lift(o1, z0), lift(o1, z1)))
        tris.append((lift(o0, z0), lift(o1, z1), lift(o0, z1)))
        # hole wall
        tris.append((lift(n0, z0), lift(n0, z1), lift(n1, z1)))
        tris.append((lift(n0, z0), lift(n1, z1), lift(n1, z0)))
    return tris


def write_ascii_cube(path: Path, size: float = 20.0) -> None:
    import sys
    from pathlib import Path as P

    scripts = P(__file__).resolve().parents[1]
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from stl_write import write_ascii_stl  # noqa: E402

    write_ascii_stl(path, cube_tris(size), name="cube")


def triangle_soup_step(n_faces: int) -> str:
    lines = [
        "ISO-10303-21;",
        "HEADER;",
        "FILE_DESCRIPTION(('triangle soup'),'2;1');",
        "FILE_NAME('soup.step','2026-01-01',('preverse'),('printables'),",
        "  ' ',' ',' ');",
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));",
        "ENDSEC;",
        "DATA;",
    ]
    for i in range(1, n_faces + 1):
        lines.append(f"#{i}=ADVANCED_FACE('',(#100),#200,.F.);")
    lines.append("#999=MANIFOLD_SOLID_BREP('soup',#1000);")
    lines.append("ENDSEC;")
    lines.append("END-ISO-10303-21;")
    return "\n".join(lines) + "\n"
