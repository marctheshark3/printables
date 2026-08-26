#!/usr/bin/env python3
"""Preview-only assembly stills from the printable STLs. Not a manufacturing body."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parents[3] / "skills" / "3d-print-validate" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from stl_io import load_binary_stl, tri_normal  # noqa: E402

CHASSIS_LENGTH = 88.0
CHASSIS_WIDTH = 58.0
DECK_T = 3.2
WALL = 2.4
MCU_L, MCU_W, MCU_T = 22.5, 18.0, 3.5
MCU_CLEAR, MCU_DEPTH = 0.4, 1.6
M2_BOSS_OD = 5.6
GEAR_L, GEAR_W, GEAR_H = 15.0, 12.0, 10.0
MOTOR_CLEAR = 0.4
SHAFT_D, SHAFT_L = 3.0, 10.0
WHEEL_OD, WHEEL_T = 40.0, 6.0
HEAD_H, HEAD_BOSS_H, HEAD_BOSS_OD = 12.0, 3.2, 10.0
LED_D = 5.2


def xf(tris, fn):
    return tuple((fn(a), fn(b), fn(c)) for a, b, c in tris)


def rot_x(p, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    x, y, z = p
    return (x, y * c - z * s, y * s + z * c)


def add(p, t):
    return (p[0] + t[0], p[1] + t[1], p[2] + t[2])


def box(origin, size):
    x0, y0, z0 = origin
    dx, dy, dz = size
    p = [
        (x0, y0, z0), (x0 + dx, y0, z0), (x0 + dx, y0 + dy, z0), (x0, y0 + dy, z0),
        (x0, y0, z0 + dz), (x0 + dx, y0, z0 + dz), (x0 + dx, y0 + dy, z0 + dz), (x0, y0 + dy, z0 + dz),
    ]
    faces = [
        (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
    ]
    return tuple((p[i], p[j], p[k]) for i, j, k in faces)


def load_body(name):
    _n, tris, _c = load_binary_stl(ROOT / "stl" / f"{name}.stl")
    return tris


def assemble():
    mcu_x = WALL + M2_BOSS_OD
    mcu_pl = MCU_L + 2 * MCU_CLEAR
    mcu_pw = MCU_W + 2 * MCU_CLEAR
    mcu_y = (CHASSIS_WIDTH - mcu_pw) / 2
    motor_box_x = GEAR_W + 2 * MOTOR_CLEAR + 2 * WALL
    motor_cx = mcu_x + mcu_pl + WALL + motor_box_x / 2
    head_x = CHASSIS_LENGTH - WALL - HEAD_BOSS_OD / 2
    cy = CHASSIS_WIDTH / 2
    axis_z = DECK_T + GEAR_H / 2
    lift = WHEEL_OD / 2 - axis_z

    chassis = xf(load_body("chassis"), lambda p: add(p, (0, 0, lift)))
    wheel = load_body("wheel")
    left = xf(xf(wheel, lambda p: rot_x(p, 90)), lambda p: add(p, (motor_cx, 0, axis_z + lift)))
    right = xf(xf(wheel, lambda p: rot_x(p, -90)), lambda p: add(p, (motor_cx, CHASSIS_WIDTH, axis_z + lift)))
    head = xf(load_body("head"), lambda p: add(p, (head_x, cy, DECK_T + HEAD_BOSS_H + lift)))

    mcu = xf(box((mcu_x + MCU_CLEAR, mcu_y + MCU_CLEAR, DECK_T - MCU_DEPTH), (MCU_L, MCU_W, MCU_T)),
             lambda p: add(p, (0, 0, lift)))
    motor_l = xf(box((motor_cx - GEAR_W / 2, WALL + MOTOR_CLEAR, DECK_T), (GEAR_W, GEAR_L, GEAR_H)),
                 lambda p: add(p, (0, 0, lift)))
    motor_r = xf(box((motor_cx - GEAR_W / 2, CHASSIS_WIDTH - WALL - MOTOR_CLEAR - GEAR_L, DECK_T),
                     (GEAR_W, GEAR_L, GEAR_H)),
                 lambda p: add(p, (0, 0, lift)))
    led = xf(box((head_x - LED_D / 2, cy - LED_D / 2, DECK_T + HEAD_BOSS_H + HEAD_H - 1 + lift),
                 (LED_D, LED_D, 4.0)),
             lambda p: p)

    return [
        (chassis, (48, 48, 52)),
        (left, (22, 22, 24)),
        (right, (22, 22, 24)),
        (head, (62, 62, 68)),
        (mcu, (46, 125, 50)),
        (motor_l, (176, 176, 180)),
        (motor_r, (176, 176, 180)),
        (led, (220, 50, 50)),
    ]


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
