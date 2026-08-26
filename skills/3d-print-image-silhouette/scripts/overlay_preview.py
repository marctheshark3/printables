#!/usr/bin/env python3
"""overlay_preview.py — plate frame + silhouette QA image from poly.json."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--poly", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--size", type=int, default=900)
    p.add_argument("--title", type=str, default="")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    meta = json.loads(args.poly.read_text(encoding="utf-8"))
    plate = float(meta["plate_mm"])
    frame = float(meta["frame_mm"])
    if meta.get("polygons"):
        polys = [[(p["x"], p["y"]) for p in poly] for poly in meta["polygons"]]
    else:
        polys = [[(p["x"], p["y"]) for p in meta["polygon"]]]
    half = plate / 2
    size = args.size
    margin = 40
    scale = (size - 2 * margin) / plate

    def to_px(x, y):
        px = margin + (x + half) * scale
        py = margin + (half - y) * scale
        return (px, py)

    img = Image.new("RGB", (size, size + 50), (18, 18, 22))
    dr = ImageDraw.Draw(img)

    o0 = to_px(-half, half)
    o1 = to_px(half, -half)
    dr.rectangle([o0[0], o0[1], o1[0], o1[1]], fill=(40, 44, 52), outline=(180, 180, 190), width=2)

    ih = half - frame
    i0 = to_px(-ih, ih)
    i1 = to_px(ih, -ih)
    dr.rectangle([i0[0], i0[1], i1[0], i1[1]], outline=(90, 90, 100), width=1)

    npts = 0
    for poly in polys:
        pts = [to_px(x, y) for x, y in poly]
        npts += len(poly)
        if len(pts) >= 3:
            dr.polygon(pts, fill=(230, 230, 235), outline=(100, 200, 255))

    title = args.title or args.poly.parent.name
    dr.text(
        (12, size + 8),
        f"{title}  plate={plate} frame={frame} polys={len(polys)} pts={npts}  QA overlay",
        fill=(200, 200, 210),
    )

    mf = float(meta.get("min_feature_mm", 1.6))
    x0, y0 = to_px(-half + 4, -half + 4)
    x1 = x0 + mf * scale
    dr.line([(x0, y0), (x1, y0)], fill=(255, 180, 80), width=3)
    dr.text((x0, y0 - 14), f"{mf}mm", fill=(255, 180, 80))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    img.save(args.out)
    print(f"overlay: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
