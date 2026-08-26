#!/usr/bin/env python3
"""Preview-only assembly stills from the printable STLs. Not a manufacturing body."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PACK = Path(__file__).resolve().parents[3]
VALIDATE = PACK / "skills" / "3d-print-validate" / "scripts"
BRIEF = PACK / "skills" / "3d-print-design-brief" / "scripts"
for path in (str(VALIDATE), str(BRIEF)):
    if path not in sys.path:
        sys.path.insert(0, path)

from assembly import place_assembly  # noqa: E402
from print_spec import load_spec  # noqa: E402
from stl_io import tri_normal  # noqa: E402

COLORS = {
    "chassis": (48, 48, 52),
    "wheel_left": (22, 22, 24),
    "wheel_right": (22, 22, 24),
    "head": (62, 62, 68),
    "mcu": (46, 125, 50),
    "drive_left": (176, 176, 180),
    "drive_right": (176, 176, 180),
}


def assemble():
    spec, errors = load_spec(ROOT / "docs/PRINT_SPEC.yaml", project=ROOT, check_files=True)
    if spec is None or errors:
        raise SystemExit("HARD: " + "; ".join(errors))
    placed = place_assembly(ROOT, spec)
    return [(tris, COLORS.get(body_id, (180, 180, 180))) for body_id, tris in placed.items()]


def look_at(eye, center, up=(0.0, 0.0, 1.0)):
    f = np.subtract(center, eye)
    f = f / np.linalg.norm(f)
    r = np.cross(f, up)
    r = r / np.linalg.norm(r)
    u = np.cross(r, f)
    return np.array(eye, dtype=np.float64), r, u, f


def project(p, eye, right, up, fwd, width, height, fov_deg=38.0):
    v = np.subtract(p, eye)
    x, y, z = np.dot(v, right), np.dot(v, up), np.dot(v, fwd)
    if z < 1.0:
        return None
    s = (0.5 * height) / math.tan(math.radians(fov_deg) / 2.0)
    return width * 0.5 + s * x / z, height * 0.5 - s * y / z, z


def rasterize(parts, eye, center, size=(1600, 1000)):
    width, height = size
    eye, right, up, fwd = look_at(eye, center)
    rgb = np.zeros((height, width, 3), dtype=np.float32)
    rgb[:, :] = (18, 18, 22)
    zbuf = np.full((height, width), 1e9, dtype=np.float32)
    light = np.array([0.45, -0.35, 0.82], dtype=np.float64)
    light = light / np.linalg.norm(light)

    for tris, color in parts:
        col = np.array(color, dtype=np.float64)
        for a, b, c in tris:
            n = np.array(tri_normal(a, b, c))
            if np.dot(n, fwd) > 0.08:
                continue
            pa, pb, pc = (project(p, eye, right, up, fwd, width, height) for p in (a, b, c))
            if pa is None or pb is None or pc is None:
                continue
            xs = (pa[0], pb[0], pc[0])
            ys = (pa[1], pb[1], pc[1])
            minx, maxx = max(0, int(math.floor(min(xs)))), min(width - 1, int(math.ceil(max(xs))))
            miny, maxy = max(0, int(math.floor(min(ys)))), min(height - 1, int(math.ceil(max(ys))))
            if minx >= maxx or miny >= maxy:
                continue
            area = (pb[0] - pa[0]) * (pc[1] - pa[1]) - (pc[0] - pa[0]) * (pb[1] - pa[1])
            if abs(area) < 1e-6:
                continue
            shade = 0.28 + 0.72 * max(0.0, float(np.dot(n, light)))
            fill = col * shade
            ax, ay, az = pa
            bx, by, bz = pb
            cx, cy, cz = pc
            for py in range(miny, maxy + 1):
                for px in range(minx, maxx + 1):
                    w0 = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
                    w1 = (cx - bx) * (py - by) - (cy - by) * (px - bx)
                    w2 = (ax - cx) * (py - cy) - (ay - cy) * (px - cx)
                    if area < 0:
                        w0, w1, w2, den = -w0, -w1, -w2, -area
                    else:
                        den = area
                    if w0 < 0 or w1 < 0 or w2 < 0:
                        continue
                    bary0, bary1, bary2 = w1 / den, w2 / den, w0 / den
                    z = bary0 * az + bary1 * bz + bary2 * cz
                    if z < zbuf[py, px]:
                        zbuf[py, px] = z
                        rgb[py, px] = fill
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")


def main() -> int:
    parts = assemble()
    out = ROOT / "renders"
    out.mkdir(exist_ok=True)
    shots = {
        "assembly.png": ((-8.0, -88.0, 108.0), (46.0, 29.0, 16.0)),
        "assembly-front.png": ((132.0, -78.0, 92.0), (52.0, 29.0, 18.0)),
    }
    for name, (eye, center) in shots.items():
        img = rasterize(parts, eye=eye, center=center)
        img.save(out / name)
        print(f"wrote {out / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
