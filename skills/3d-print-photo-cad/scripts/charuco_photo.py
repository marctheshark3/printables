"""ChArUco board and photo scale for photo-derived CAD.

A square is 15.0 mm only if the sheet was printed at 100% and a ruler
confirmed one square. This script does not invent part geometry.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SQUARE_MM = 15.0
MARKER_MM = 11.0
SQUARES_X = 12
SQUARES_Y = 16
PX_PER_MM = 10
MIN_CORNERS = 12
SQUARE_TOL_MM = 0.15


def median_nearest_gap(
    points: list[tuple[float, float]],
    lo: float = 1.0,
    hi: float = 40.0,
) -> float | None:
    """Median of each point's nearest neighbor, in the same units as points."""
    gaps: list[float] = []
    for i, (x, y) in enumerate(points):
        best: float | None = None
        for j, (u, v) in enumerate(points):
            if i == j:
                continue
            dist = ((x - u) ** 2 + (y - v) ** 2) ** 0.5
            if lo < dist < hi and (best is None or dist < best):
                best = dist
        if best is not None:
            gaps.append(best)
    if not gaps:
        return None
    gaps.sort()
    mid = len(gaps) // 2
    if len(gaps) % 2:
        return gaps[mid]
    return (gaps[mid - 1] + gaps[mid]) / 2.0


def parse_span(text: str) -> tuple[float, float, float, float]:
    parts = [part.strip() for part in text.split(",")]
    if len(parts) != 4:
        raise ValueError("span needs x1,y1,x2,y2")
    return tuple(float(part) for part in parts)  # type: ignore[return-value]


def apply_homography(h: list[list[float]], x: float, y: float) -> tuple[float, float]:
    den = h[2][0] * x + h[2][1] * y + h[2][2]
    if abs(den) < 1e-12:
        raise ValueError("homography degenerate")
    return (
        (h[0][0] * x + h[0][1] * y + h[0][2]) / den,
        (h[1][0] * x + h[1][1] * y + h[1][2]) / den,
    )


def span_mm(
    h: list[list[float]],
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> float:
    """Board-plane distance. Valid only if both points lie on the paper."""
    u1, v1 = apply_homography(h, x1, y1)
    u2, v2 = apply_homography(h, x2, y2)
    return ((u1 - u2) ** 2 + (v1 - v2) ** 2) ** 0.5


def square_within_tol(
    recovered: float | None,
    nominal: float = SQUARE_MM,
    tol: float = SQUARE_TOL_MM,
) -> bool:
    if recovered is None:
        return False
    return abs(round(recovered * 1000) - round(nominal * 1000)) <= round(tol * 1000)


def require_cv():
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("opencv-python and numpy are required for ChArUco measure", file=sys.stderr)
        raise SystemExit(2)
    return cv2, np


def board(cv2):
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_100)
    return cv2.aruco.CharucoBoard(
        (SQUARES_X, SQUARES_Y),
        SQUARE_MM / 1000.0,
        MARKER_MM / 1000.0,
        dictionary,
    )


def write_board(out_dir: Path) -> None:
    cv2, _np = require_cv()
    out_dir.mkdir(parents=True, exist_ok=True)
    width = int(SQUARES_X * SQUARE_MM * 12)
    height = int(SQUARES_Y * SQUARE_MM * 12)
    image = board(cv2).generateImage((width, height), marginSize=0)
    png = out_dir / "charuco-15mm.png"
    if not cv2.imwrite(str(png), image):
        raise SystemExit(f"imwrite failed {png}")
    html = out_dir / "print.html"
    html.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ChArUco 15 mm — print at 100%</title>
<style>
@page {{ size: letter; margin: 12mm; }}
body {{ margin: 0; font: 14px/1.4 system-ui, sans-serif; }}
img {{ width: {SQUARES_X * SQUARE_MM:.0f}mm; height: {SQUARES_Y * SQUARE_MM:.0f}mm; display: block; page-break-after: always; break-after: page; }}
p {{ max-width: 180mm; }}
</style>
</head>
<body>
<img src="charuco-15mm.png" alt="ChArUco board, 15 mm squares">
<p>Print at 100%. No fit-to-page. One square must measure <b>15.0 mm</b> with a ruler before any photo counts. Part in the middle, board visible on all four sides. This page checks the board. It does not measure a face raised above the paper.</p>
</body>
</html>
"""
    )
    print(f"WROTE {png.name} {png.stat().st_size}")
    print(f"WROTE {html.name}")


def measure(photo: Path, out_dir: Path, span: tuple[float, float, float, float] | None = None) -> int:
    cv2, np = require_cv()
    image = cv2.imread(str(photo))
    if image is None:
        print(json.dumps({"ok": False, "reason": "unreadable", "photo": photo.name}))
        return 1
    detected = board(cv2)
    corners, ids, _markers, marker_ids = cv2.aruco.CharucoDetector(detected).detectBoard(image)
    n_corners = 0 if corners is None else len(corners)
    n_markers = 0 if marker_ids is None else len(marker_ids)
    if n_corners < MIN_CORNERS:
        print(json.dumps({
            "ok": False,
            "corners": n_corners,
            "markers": n_markers,
            "reason": "board not in frame",
            "photo": photo.name,
        }))
        return 1
    obj_m, img_pts = detected.matchImagePoints(corners, ids)
    obj_mm = obj_m.reshape(-1, 3)[:, :2] * 1000.0
    img_pts = img_pts.reshape(-1, 2)
    homography, mask = cv2.findHomography(img_pts, obj_mm, cv2.RANSAC, 1.0)
    if homography is None:
        print(json.dumps({"ok": False, "reason": "no homography", "corners": n_corners}))
        return 1
    inliers = int(mask.sum()) if mask is not None else 0
    scale = np.array([[PX_PER_MM, 0, 0], [0, PX_PER_MM, 0], [0, 0, 1]], dtype=np.float64)
    width = int(SQUARES_X * SQUARE_MM * PX_PER_MM)
    height = int(SQUARES_Y * SQUARE_MM * PX_PER_MM)
    flat = cv2.warpPerspective(image, scale @ homography, (width, height), borderValue=255)
    # Homography is the paper plane. A raised face is enlarged; do not treat those pixels as mm.
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = photo.stem
    rectified = out_dir / f"{stem}-board-plane.png"
    if not cv2.imwrite(str(rectified), flat):
        raise SystemExit(f"imwrite failed {rectified.name}")
    projected = cv2.perspectiveTransform(img_pts.reshape(-1, 1, 2), homography).reshape(-1, 2)
    points = [(float(p[0]), float(p[1])) for p in projected]
    recovered = median_nearest_gap(points)
    recovered_r = round(float(recovered), 3) if recovered is not None else None
    ok = square_within_tol(recovered)
    report = {
        "ok": ok,
        "source": "photo-derived",
        "photo": photo.name,
        "rectified": rectified.name,
        "corners": n_corners,
        "markers": n_markers,
        "inliers": inliers,
        "square_mm": SQUARE_MM,
        "square_tol_mm": SQUARE_TOL_MM,
        "recovered_square_mm": recovered_r,
        "px_per_mm": PX_PER_MM,
        "mm_per_px": round(1.0 / PX_PER_MM, 5),
        "board_mm": [SQUARES_X * SQUARE_MM, SQUARES_Y * SQUARE_MM],
        "plane": "Board plane only. Raised faces are not metric. Z is not in this photo.",
        "part_px_are_metric": False,
        "part_dimensions_emitted": False,
        "coplanar_asserted": False,
        "coplanar_verified": False,
        "print_check": "Ruler must read 15.0 mm on one printed square or every length is wrong.",
    }
    if span is not None and ok:
        dist = span_mm(homography.tolist(), *span)
        report["span_mm"] = round(dist, 3)
        report["part_dimensions_emitted"] = True
        report["coplanar_asserted"] = True
        report["span_note"] = "operator-asserted board-plane span; not verified; not a raised face"
    if not ok:
        report["reason"] = "recovered square outside 0.15 mm"
    meta = out_dir / f"{stem}-measure.json"
    meta.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("photo", nargs="?", help="photo that contains the printed board")
    parser.add_argument("--out", required=True, help="directory for the board or the measure files")
    parser.add_argument("--board", action="store_true", help="write the printable board")
    parser.add_argument(
        "--coplanar-span",
        help="x1,y1,x2,y2 in original photo pixels, both on the paper. Not a raised face.",
    )
    args = parser.parse_args(argv)
    out = Path(args.out)
    if args.board:
        write_board(out)
        return 0
    span = None
    if args.coplanar_span:
        try:
            span = parse_span(args.coplanar_span)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
    if not args.photo:
        print("photo required unless --board", file=sys.stderr)
        return 2
    return measure(Path(args.photo), out, span)


if __name__ == "__main__":
    raise SystemExit(main())
