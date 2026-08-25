#!/usr/bin/env python3
"""trace_silhouette.py — PNG → binary + simplified polygon (mm) + SVG.

Pure Python 3 + Pillow. No numpy.

Usage:
  trace_silhouette.py --input icon.png --out-dir trace/name \\
      --plate 160 --frame 14 --min-feature-mm 1.6 --hole-policy filled
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import deque
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageOps

Point = Tuple[float, float]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Trace silhouette PNG to polygon mm")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--plate", type=float, default=160.0)
    p.add_argument("--frame", type=float, default=14.0)
    p.add_argument("--min-feature-mm", type=float, default=1.6)
    p.add_argument(
        "--hole-policy",
        choices=["filled", "islands-bridged", "islands-loose"],
        default="filled",
    )
    p.add_argument("--threshold", type=int, default=128, help="0-255; below → black fg")
    p.add_argument("--invert", action="store_true", help="Treat light as foreground")
    p.add_argument("--epsilon-mm", type=float, default=0.45, help="RDP simplify epsilon")
    p.add_argument("--work-size", type=int, default=900, help="Working raster max side px")
    p.add_argument(
        "--components",
        choices=["largest", "significant"],
        default="largest",
        help="largest=icons; significant=multi-letter words (keep all ink CCs ≥2%)",
    )
    return p.parse_args()


def to_binary(im: Image.Image, threshold: int, invert: bool) -> Image.Image:
    g = ImageOps.grayscale(im)
    # Foreground = dark by default (black silhouette on white)
    bw = g.point(lambda v: 0 if (v < threshold) ^ invert else 255, mode="1")
    return bw.convert("L")


def keep_components(mask: Image.Image, mode: str = "largest") -> Image.Image:
    """Keep black (0) components.

    mode:
      largest — single biggest CC (icons)
      significant — all CCs ≥ 2% of total black ink (multi-letter words)
    """
    w, h = mask.size
    px = mask.load()
    visited = [[False] * w for _ in range(h)]
    comps: List[List[Tuple[int, int]]] = []
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))

    for y in range(h):
        for x in range(w):
            if px[x, y] != 0 or visited[y][x]:
                continue
            q = deque([(x, y)])
            visited[y][x] = True
            comp: List[Tuple[int, int]] = []
            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                for dx, dy in dirs:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and px[nx, ny] == 0:
                        visited[ny][nx] = True
                        q.append((nx, ny))
            comps.append(comp)

    if not comps:
        return mask

    total_ink = sum(len(c) for c in comps)
    if mode == "significant":
        thr = max(20, int(0.02 * total_ink))
        keep = [c for c in comps if len(c) >= thr]
        if not keep:
            keep = [max(comps, key=len)]
    else:
        keep = [max(comps, key=len)]

    out = Image.new("L", (w, h), 255)
    op = out.load()
    for comp in keep:
        for x, y in comp:
            op[x, y] = 0
    return out


def largest_component(mask: Image.Image) -> Image.Image:
    return keep_components(mask, mode="largest")


def ensure_white_border(mask: Image.Image, pad: int = 4) -> Image.Image:
    """Pad with white so exterior flood-fill always has a seed."""
    w, h = mask.size
    out = Image.new("L", (w + 2 * pad, h + 2 * pad), 255)
    out.paste(mask, (pad, pad))
    return out


def fill_holes(mask: Image.Image) -> Image.Image:
    """Fill white holes inside black silhouette via flood-fill from border.

    Requires white margin (use ensure_white_border first). Seeds only from white.
    """
    w, h = mask.size
    rgba = mask.convert("RGB")
    px = rgba.load()
    # Find a guaranteed white border seed
    seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0)]
    seeded = False
    for sx, sy in seeds:
        if px[sx, sy][0] > 200:
            ImageDraw.floodfill(rgba, (sx, sy), (0, 0, 255), thresh=30)
            seeded = True
            break
    if not seeded:
        # No white corner — do not destroy the mask
        return mask

    px = rgba.load()
    out = Image.new("L", (w, h), 255)
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r == 0 and g == 0 and b == 255:
                op[x, y] = 255  # exterior
            else:
                # original black + interior whites → filled silhouette
                op[x, y] = 0
    return out


def morph_close_open(mask: Image.Image, radius_px: int) -> Image.Image:
    """Light morphological close only (dilate+erode). Avoid open that erodes thin horns."""
    if radius_px < 1:
        return mask
    # Silhouette is black (0); invert so fg is white for Max/Min
    inv = ImageOps.invert(mask.convert("L"))
    # PIL MaxFilter size must be odd
    k = max(3, radius_px * 2 + 1)
    if k % 2 == 0:
        k += 1
    # close only — join hairline gaps without eating thin features twice
    inv = inv.filter(ImageFilter.MaxFilter(k))
    inv = inv.filter(ImageFilter.MinFilter(k))
    return ImageOps.invert(inv)


def moore_trace(mask: Image.Image) -> List[Tuple[int, int]]:
    """Trace outer boundary of black (0) region, clockwise-ish."""
    w, h = mask.size
    px = mask.load()
    # find start: leftmost then topmost black with white above or on top row
    start = None
    for y in range(h):
        for x in range(w):
            if px[x, y] == 0:
                start = (x, y)
                break
        if start:
            break
    if not start:
        return []

    # 8-connected neighborhood clockwise from W
    # indices 0..7: E, SE, S, SW, W, NW, N, NE
    nb = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]

    def is_fg(x, y):
        return 0 <= x < w and 0 <= y < h and px[x, y] == 0

    contour: List[Tuple[int, int]] = []
    x, y = start
    # backtrack direction: came from west initially
    back = 4  # W
    for _ in range(w * h * 4):
        contour.append((x, y))
        # start search from back+1
        found = False
        for k in range(8):
            di = (back + 1 + k) % 8
            dx, dy = nb[di]
            nx, ny = x + dx, y + dy
            if is_fg(nx, ny):
                # new back is opposite of arrival
                back = (di + 4) % 8
                x, y = nx, ny
                found = True
                break
        if not found:
            break
        if (x, y) == start and len(contour) > 8:
            break
    return contour


def rdp(points: Sequence[Point], epsilon: float) -> List[Point]:
    if len(points) < 3:
        return list(points)

    def dist_point_line(p, a, b):
        ax, ay = a
        bx, by = b
        px, py = p
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

    def rec(pts):
        if len(pts) < 3:
            return list(pts)
        a, b = pts[0], pts[-1]
        idx, dmax = 0, 0.0
        for i in range(1, len(pts) - 1):
            d = dist_point_line(pts[i], a, b)
            if d > dmax:
                idx, dmax = i, d
        if dmax > epsilon:
            left = rec(pts[: idx + 1])
            right = rec(pts[idx:])
            return left[:-1] + right
        return [a, b]

    return rec(list(points))


def ink_bbox(mask: Image.Image) -> Tuple[int, int, int, int]:
    """Bounding box of black ink (minx, miny, maxx, maxy)."""
    bb = mask.getbbox()
    if not bb:
        w, h = mask.size
        return (0, 0, w - 1, h - 1)
    # getbbox on L image treats non-zero as content — our ink is 0.
    # Invert to use getbbox on ink.
    inv = ImageOps.invert(mask.convert("L"))
    bb = inv.getbbox()
    if not bb:
        w, h = mask.size
        return (0, 0, w - 1, h - 1)
    return bb  # left, upper, right, lower


def contours_from_mask(mask: Image.Image, components: str) -> List[List[Tuple[int, int]]]:
    """Return list of pixel contours (one per kept component)."""
    w, h = mask.size
    px = mask.load()
    visited = [[False] * w for _ in range(h)]
    comps: List[List[Tuple[int, int]]] = []
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for y in range(h):
        for x in range(w):
            if px[x, y] != 0 or visited[y][x]:
                continue
            q = deque([(x, y)])
            visited[y][x] = True
            comp: List[Tuple[int, int]] = []
            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                for dx, dy in dirs:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and px[nx, ny] == 0:
                        visited[ny][nx] = True
                        q.append((nx, ny))
            comps.append(comp)
    if not comps:
        return []
    total = sum(len(c) for c in comps)
    if components == "significant":
        thr = max(20, int(0.02 * total))
        comps = [c for c in comps if len(c) >= thr] or [max(comps, key=len)]
    else:
        comps = [max(comps, key=len)]

    contours: List[List[Tuple[int, int]]] = []
    for comp in comps:
        # Build tiny mask for this component and moore-trace
        m = Image.new("L", (w, h), 255)
        mp = m.load()
        for x, y in comp:
            mp[x, y] = 0
        c = moore_trace(m)
        if len(c) >= 10:
            contours.append(c)
    return contours


def contour_to_mm(
    contour: Sequence[Tuple[int, int]],
    plate: float,
    frame: float,
    global_bbox: Tuple[int, int, int, int],
) -> List[Point]:
    """Map pixel contour into plate inner box using shared global ink bbox."""
    if not contour:
        return []
    minx, miny, maxx, maxy = global_bbox
    bw = max(maxx - minx, 1)
    bh = max(maxy - miny, 1)
    inner = plate - 2 * frame
    pad = 0.92
    scale = pad * min(inner / bw, inner / bh)
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    out: List[Point] = []
    for x, y in contour:
        mx = (x - cx) * scale
        my = -(y - cy) * scale  # image Y down → OpenSCAD Y up
        out.append((mx, my))
    return out


def write_svg(path: Path, polys: Sequence[Sequence[Point]], plate: float) -> None:
    half = plate / 2
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-half} {-half} {plate} {plate}">',
        f'<rect x="{-half}" y="{-half}" width="{plate}" height="{plate}" fill="#eee" stroke="#333"/>',
    ]
    for poly in polys:
        lines.append(
            '<polygon points="'
            + " ".join(f"{x:.3f},{-y:.3f}" for x, y in poly)
            + '" fill="#111" fill-rule="evenodd"/>'
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.hole_policy == "islands-loose":
        print("ERROR: hole-policy islands-loose forbidden for this pipeline", file=sys.stderr)
        return 2
    if not args.input.is_file():
        print(f"ERROR: missing input {args.input}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    im = Image.open(args.input).convert("RGB")
    # downscale for stable tracing
    im.thumbnail((args.work_size, args.work_size), Image.Resampling.LANCZOS)

    comp_mode = args.components
    bw = to_binary(im, args.threshold, args.invert)
    bw = ensure_white_border(bw, pad=8)
    bw = keep_components(bw, mode=comp_mode)
    if args.hole_policy == "filled":
        bw = fill_holes(bw)
        bw = keep_components(bw, mode=comp_mode)

    # Light close only — radius capped so we never flood the frame
    inner = args.plate - 2 * args.frame
    gbb = ink_bbox(bw)
    bb_w = max(gbb[2] - gbb[0], 1)
    px_per_mm = bb_w / (inner * 0.92)
    radius_px = max(1, min(3, int(round(0.35 * args.min_feature_mm * px_per_mm))))
    bw = morph_close_open(bw, radius_px)
    bw = ensure_white_border(bw, pad=4)
    bw = keep_components(bw, mode=comp_mode)
    if args.hole_policy == "filled":
        bw = fill_holes(bw)
        bw = keep_components(bw, mode=comp_mode)

    # Safety: foreground must not exceed 85% of pixels (detect fill blow-up)
    hist = bw.histogram()
    black = hist[0] if hist else 0
    total = bw.size[0] * bw.size[1]
    frac = black / max(total, 1)
    if frac > 0.85:
        print(
            f"ERROR: foreground covers {frac*100:.1f}% of raster — fill/morph blow-up",
            file=sys.stderr,
        )
        return 1

    binary_path = args.out_dir / "binary.png"
    bw.save(binary_path)

    gbb = ink_bbox(bw)
    contours = contours_from_mask(bw, components=comp_mode)
    if not contours:
        print("ERROR: no contours — check threshold/invert", file=sys.stderr)
        return 1

    polys_mm: List[List[Point]] = []
    for contour in contours:
        step = max(1, len(contour) // 4000)
        contour_s = contour[::step]
        poly_mm = contour_to_mm(contour_s, args.plate, args.frame, gbb)
        poly_mm = rdp(poly_mm, args.epsilon_mm)
        if poly_mm and poly_mm[0] != poly_mm[-1]:
            poly_mm.append(poly_mm[0])
        if len(poly_mm) >= 4:
            polys_mm.append(poly_mm)

    if not polys_mm:
        print("ERROR: simplified polygons degenerate", file=sys.stderr)
        return 1

    all_pts = [p for poly in polys_mm for p in poly]
    primary = polys_mm[0]
    meta = {
        "source": str(args.input.resolve()),
        "plate_mm": args.plate,
        "frame_mm": args.frame,
        "thickness_hint_mm": 2.0,
        "min_feature_mm": args.min_feature_mm,
        "hole_policy": args.hole_policy,
        "components": comp_mode,
        "epsilon_mm": args.epsilon_mm,
        "n_polygons": len(polys_mm),
        "n_points": sum(len(p) for p in polys_mm),
        "bbox_mm": {
            "min_x": min(p[0] for p in all_pts),
            "max_x": max(p[0] for p in all_pts),
            "min_y": min(p[1] for p in all_pts),
            "max_y": max(p[1] for p in all_pts),
        },
        # backward-compat single polygon = first
        "polygon": [{"x": x, "y": y} for x, y in primary],
        "polygons": [
            [{"x": x, "y": y} for x, y in poly] for poly in polys_mm
        ],
    }
    poly_path = args.out_dir / "poly.json"
    poly_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_svg(args.out_dir / "silhouette.svg", polys_mm, args.plate)

    print(f"binary: {binary_path}")
    print(f"poly:   {poly_path} polygons={len(polys_mm)} points={meta['n_points']}")
    print(f"svg:    {args.out_dir / 'silhouette.svg'}")
    print(f"bbox_mm: {meta['bbox_mm']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
