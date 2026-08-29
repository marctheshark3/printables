#!/usr/bin/env python3
"""Split an oversized bar into two bodies with alignment keys. Never scale."""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

TEMPLATE = (
    Path(__file__).resolve().parent.parent.parent
    / "3d-print-openscad"
    / "templates"
    / "split_for_bed.scad"
)

Vec3 = Tuple[float, float, float]
Tri = Tuple[Vec3, Vec3, Vec3]


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def add_quad(tris: List[Tri], a: Vec3, b: Vec3, c: Vec3, d: Vec3, outward: Vec3) -> None:
    n = _cross(_sub(b, a), _sub(c, a))
    if _dot(n, outward) >= 0:
        tris.append((a, b, c))
        tris.append((a, c, d))
    else:
        tris.append((a, c, b))
        tris.append((a, d, c))


def write_binary_stl(path: Path, triangles: Sequence[Tri]) -> None:
    data = bytearray(80)
    data.extend(struct.pack("<I", len(triangles)))
    for a, b, c in triangles:
        data.extend(struct.pack("<12fH", 0, 0, 0, *a, *b, *c, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def bbox(triangles: Sequence[Tri]) -> Tuple[float, float, float]:
    xs = [p[0] for tri in triangles for p in tri]
    ys = [p[1] for tri in triangles for p in tri]
    zs = [p[2] for tri in triangles for p in tri]
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def box_with_pin(
    length: float, width: float, height: float, pin_len: float, pin_w: float
) -> List[Tri]:
    """One watertight shell: bar plus rectangular key on +X."""
    l, w, h = length, width, height
    y0 = (w - pin_w) / 2.0
    y1 = y0 + pin_w
    z0 = (h - pin_w) / 2.0
    z1 = z0 + pin_w
    m000, ml00, mlw0, m0w0 = (0.0, 0.0, 0.0), (l, 0.0, 0.0), (l, w, 0.0), (0.0, w, 0.0)
    m00h, ml0h, mlwh, m0wh = (0.0, 0.0, h), (l, 0.0, h), (l, w, h), (0.0, w, h)
    p00, p10, p11, p01 = (l, y0, z0), (l, y1, z0), (l, y1, z1), (l, y0, z1)
    q00 = (l + pin_len, y0, z0)
    q10 = (l + pin_len, y1, z0)
    q11 = (l + pin_len, y1, z1)
    q01 = (l + pin_len, y0, z1)
    plus_x = (1.0, 0.0, 0.0)
    tris: List[Tri] = []
    add_quad(tris, m000, ml00, mlw0, m0w0, (0.0, 0.0, -1.0))
    add_quad(tris, m00h, m0wh, mlwh, ml0h, (0.0, 0.0, 1.0))
    add_quad(tris, m000, m00h, ml0h, ml00, (0.0, -1.0, 0.0))
    add_quad(tris, m0w0, mlw0, mlwh, m0wh, (0.0, 1.0, 0.0))
    add_quad(tris, m000, m0w0, m0wh, m00h, (-1.0, 0.0, 0.0))
    add_quad(tris, ml00, mlw0, p10, p00, plus_x)
    add_quad(tris, mlw0, mlwh, p11, p10, plus_x)
    add_quad(tris, mlwh, ml0h, p01, p11, plus_x)
    add_quad(tris, ml0h, ml00, p00, p01, plus_x)
    add_quad(tris, p00, q00, q01, p01, (0.0, -1.0, 0.0))
    add_quad(tris, p10, p11, q11, q10, (0.0, 1.0, 0.0))
    add_quad(tris, p00, p10, q10, q00, (0.0, 0.0, -1.0))
    add_quad(tris, p01, q01, q11, p11, (0.0, 0.0, 1.0))
    add_quad(tris, q00, q10, q11, q01, plus_x)
    return tris


def box_with_pocket(
    length: float, width: float, height: float, pocket_depth: float, pocket_w: float
) -> List[Tri]:
    """One watertight shell: bar minus rectangular socket on −X."""
    l, w, h = length, width, height
    y0 = (w - pocket_w) / 2.0
    y1 = y0 + pocket_w
    z0 = (h - pocket_w) / 2.0
    z1 = z0 + pocket_w
    pd = pocket_depth
    m000, ml00, mlw0, m0w0 = (0.0, 0.0, 0.0), (l, 0.0, 0.0), (l, w, 0.0), (0.0, w, 0.0)
    m00h, ml0h, mlwh, m0wh = (0.0, 0.0, h), (l, 0.0, h), (l, w, h), (0.0, w, h)
    r00, r10, r11, r01 = (0.0, y0, z0), (0.0, y1, z0), (0.0, y1, z1), (0.0, y0, z1)
    s00, s10, s11, s01 = (pd, y0, z0), (pd, y1, z0), (pd, y1, z1), (pd, y0, z1)
    minus_x = (-1.0, 0.0, 0.0)
    tris: List[Tri] = []
    add_quad(tris, m000, ml00, mlw0, m0w0, (0.0, 0.0, -1.0))
    add_quad(tris, m00h, m0wh, mlwh, ml0h, (0.0, 0.0, 1.0))
    add_quad(tris, m000, m00h, ml0h, ml00, (0.0, -1.0, 0.0))
    add_quad(tris, m0w0, mlw0, mlwh, m0wh, (0.0, 1.0, 0.0))
    add_quad(tris, ml00, ml0h, mlwh, mlw0, (1.0, 0.0, 0.0))
    add_quad(tris, m000, m0w0, r10, r00, minus_x)
    add_quad(tris, m0w0, m0wh, r11, r10, minus_x)
    add_quad(tris, m0wh, m00h, r01, r11, minus_x)
    add_quad(tris, m00h, m000, r00, r01, minus_x)
    add_quad(tris, s00, s10, s11, s01, minus_x)
    add_quad(tris, r00, s00, s01, r01, (0.0, 1.0, 0.0))
    add_quad(tris, r10, r11, s11, s10, (0.0, -1.0, 0.0))
    add_quad(tris, r00, r10, s10, s00, (0.0, 0.0, 1.0))
    add_quad(tris, r01, s01, s11, r11, (0.0, 0.0, -1.0))
    return tris


def split_bar(
    *,
    length_mm: float,
    envelope: tuple[float, float, float],
    clearance_per_side_mm: float,
    width_mm: float,
    height_mm: float,
    pin_len_mm: float,
    pin_w_mm: float,
    out: Path,
) -> dict:
    if length_mm <= 0:
        raise SystemExit("HARD: length_mm must be positive")
    half = length_mm / 2.0
    ex, ey, ez = envelope
    a_len = half
    b_len = half
    if a_len + pin_len_mm >= ex or b_len >= ex or width_mm >= ey or height_mm >= ez:
        raise SystemExit(
            "HARD: a half still exceeds the envelope; split does not scale the part"
        )

    pin_clear = pin_w_mm + 2.0 * clearance_per_side_mm
    body_a = box_with_pin(a_len, width_mm, height_mm, pin_len_mm, pin_w_mm)
    body_b = box_with_pocket(b_len, width_mm, height_mm, pin_len_mm, pin_clear)

    out.mkdir(parents=True, exist_ok=True)
    path_a = out / "bar-a.stl"
    path_b = out / "bar-b.stl"
    write_binary_stl(path_a, body_a)
    write_binary_stl(path_b, body_b)

    scad = out / "bar-split.scad"
    scad.write_text(
        "\n".join(
            [
                "// Generated split-for-bed parameters. Printable union is the template.",
                f"bar_length_mm = {length_mm};",
                f"bar_width_mm = {width_mm};",
                f"bar_height_mm = {height_mm};",
                f"clearance_per_side_mm = {clearance_per_side_mm};",
                f"pin_len_mm = {pin_len_mm};",
                f"pin_w_mm = {pin_w_mm};",
                f"pin_clear_mm = {pin_clear};",
                f"envelope_mm = [{ex}, {ey}, {ez}];",
                "",
            ]
        ),
        encoding="utf-8",
    )
    if TEMPLATE.is_file():
        (out / "split_for_bed.scad").write_text(
            TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8"
        )

    report = {
        "bodies": [
            {
                "path": path_a.name,
                "body": "bar-a",
                "expected_shells": 1,
                "bbox_mm": list(bbox(body_a)),
            },
            {
                "path": path_b.name,
                "body": "bar-b",
                "expected_shells": 1,
                "bbox_mm": list(bbox(body_b)),
            },
        ],
        "clearance_per_side_mm": clearance_per_side_mm,
        "scaled": False,
        "source_length_mm": length_mm,
    }
    (out / "split.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Split a bar that exceeds the build envelope")
    parser.add_argument("--length-mm", type=float, required=True)
    parser.add_argument("--envelope-mm", type=float, nargs=3, required=True, metavar=("X", "Y", "Z"))
    parser.add_argument("--clearance-per-side-mm", type=float, required=True)
    parser.add_argument("--width-mm", type=float, default=20.0)
    parser.add_argument("--height-mm", type=float, default=20.0)
    parser.add_argument("--pin-len-mm", type=float, default=8.0)
    parser.add_argument("--pin-w-mm", type=float, default=6.0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = split_bar(
        length_mm=args.length_mm,
        envelope=tuple(args.envelope_mm),
        clearance_per_side_mm=args.clearance_per_side_mm,
        width_mm=args.width_mm,
        height_mm=args.height_mm,
        pin_len_mm=args.pin_len_mm,
        pin_w_mm=args.pin_w_mm,
        out=args.out,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
