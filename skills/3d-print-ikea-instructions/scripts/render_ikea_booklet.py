#!/usr/bin/env python3
"""IKEA-style required-sequence sheets from an OCC dump.

One new solid per step. Exploded line art plus a dashed seat.
Not a fastener plan. Not an IKEA manual.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

COS30 = 0.8660254037844386
SIN30 = 0.5
SOURCES = {"occ-step", "occ-brep"}
ORDER_RULE = "centroid z, then y, then x, then name"
NOTE = "This sequence is required. Not an IKEA manual. Not print approval."
OLD_STROKE = "#1c1b18"
GHOST_STROKE = "#8a8478"


class PlanError(ValueError):
    pass


def centroid(vertices: list) -> tuple[float, float, float]:
    if len(vertices) < 3:
        raise PlanError("part has no vertices")
    n = len(vertices)
    x = y = z = 0.0
    for v in vertices:
        if len(v) != 3:
            raise PlanError("vertex is not xyz")
        fx, fy, fz = float(v[0]), float(v[1]), float(v[2])
        if fx != fx or fy != fy or fz != fz:
            raise PlanError("vertex is not finite")
        x += fx
        y += fy
        z += fz
    return (x / n, y / n, z / n)


def _edges(part: dict) -> list:
    edges = part.get("edges") or []
    if not edges:
        name = part.get("instance") or part.get("id") or "part"
        raise PlanError(f"{name} has no BREP edges")
    return edges


def _shift(edges: list, dx: float, dy: float = 0.0, dz: float = 0.0) -> list:
    shifted = []
    for seg in edges:
        if len(seg) != 2:
            raise PlanError("edge is not a segment")
        shifted.append(
            [[float(p[0]) + dx, float(p[1]) + dy, float(p[2]) + dz] for p in seg]
        )
    return shifted


def project(x: float, y: float, z: float) -> tuple[float, float]:
    return ((x - y) * COS30, -(z + (x + y) * SIN30))


def _points(edges: list) -> list[tuple[float, float]]:
    pts = []
    for seg in edges:
        for p in seg:
            pts.append(project(float(p[0]), float(p[1]), float(p[2])))
    return pts


def _fit(points: list[tuple[float, float]], width: float, height: float, pad: float = 18):
    if not points:
        return pad, pad, 1.0
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    spanx = max(maxx - minx, 1e-6)
    spany = max(maxy - miny, 1e-6)
    scale = min((width - 2 * pad) / spanx, (height - 2 * pad) / spany)
    ox = pad - minx * scale + ((width - 2 * pad) - spanx * scale) / 2
    oy = pad - miny * scale + ((height - 2 * pad) - spany * scale) / 2
    return ox, oy, scale


def _path(edges: list, ox: float, oy: float, scale: float) -> str:
    chunks = []
    for seg in edges:
        ax, ay = project(float(seg[0][0]), float(seg[0][1]), float(seg[0][2]))
        bx, by = project(float(seg[1][0]), float(seg[1][1]), float(seg[1][2]))
        chunks.append(
            f"M{ox + ax * scale:.2f},{oy + ay * scale:.2f}L{ox + bx * scale:.2f},{oy + by * scale:.2f}"
        )
    return "".join(chunks)


def _name(part: dict, index: int) -> str:
    return str(part.get("instance") or part.get("id") or f"solid-{index}")


def _rows(parts: list) -> list[dict]:
    rows = []
    for i, part in enumerate(parts):
        if not isinstance(part, dict):
            raise PlanError(f"part[{i}] is not an object")
        verts = part.get("vertices") or []
        rows.append({"part": part, "id": _name(part, i), "centroid": centroid(verts), "edges": _edges(part)})
    rows.sort(key=lambda row: (row["centroid"][2], row["centroid"][1], row["centroid"][0], row["id"]))
    return rows


def apply_order(rows: list[dict], order: list[str]) -> list[dict]:
    by_id = {}
    for row in rows:
        if row["id"] in by_id:
            raise PlanError(f"duplicate instance {row['id']}")
        by_id[row["id"]] = row
    if len(order) != len(rows):
        raise PlanError("order must name every part once")
    picked = []
    seen = set()
    for name in order:
        if name in seen or name not in by_id:
            raise PlanError(f"order name missing or repeated: {name}")
        seen.add(name)
        picked.append(by_id[name])
    return picked


def _span_x(rows: list[dict]) -> float:
    xs = []
    for row in rows:
        for seg in row["edges"]:
            for p in seg:
                xs.append(float(p[0]))
    if not xs:
        return 20.0
    return max(max(xs) - min(xs), 10.0)


def _svg(groups: list[tuple[list, str, float, str]], arrow: tuple | None, *, width: int, height: int) -> str:
    points = []
    for edges, _stroke, _width, _dash in groups:
        points.extend(_points(edges))
    if arrow:
        points.append(project(*arrow[0]))
        points.append(project(*arrow[1]))
    ox, oy, scale = _fit(points, width, height)
    body = []
    for edges, stroke, stroke_width, dash in groups:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        body.append(
            f'<path d="{_path(edges, ox, oy, scale)}" fill="none" stroke="{stroke}" '
            f'stroke-width="{stroke_width}"{dash_attr} stroke-linecap="square"/>'
        )
    if arrow:
        ax, ay = project(*arrow[0])
        bx, by = project(*arrow[1])
        x1, y1 = ox + ax * scale, oy + ay * scale
        x2, y2 = ox + bx * scale, oy + by * scale
        body.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{OLD_STROKE}" stroke-width="1.6" marker-end="url(#arr)"/>'
        )
    return (
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        '<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">'
        f'<path d="M0,0 L7,3 L0,6 Z" fill="{OLD_STROKE}"/></marker></defs>'
        + "".join(body)
        + "</svg>"
    )


def booklet_html(dump: dict, *, title: str = "", order: list[str] | None = None) -> str:
    if not isinstance(dump, dict):
        raise PlanError("dump must be an object")
    if dump.get("source") not in SOURCES:
        raise PlanError("dump.source must be occ-step (CAD), not a mesh export")
    parts = dump.get("parts")
    if not isinstance(parts, list) or not parts:
        raise PlanError("dump.parts is empty")
    rows = _rows(parts)
    if order:
        rows = apply_order(rows, order)
    dx = _span_x(rows) * 0.45 + 8.0
    safe_title = html.escape(title or str(dump.get("name") or "Assembly"))
    sheets = [
        "<section class=\"sheet\" data-step=\"0\">"
        f"<h1>{safe_title}</h1>"
        f"<p class=\"note\">{html.escape(NOTE)}</p>"
        "<p class=\"note\">One part per step. Follow the numbers. "
        "A dashed outline is the seat. The arrow is a drawing aid, not a fastener.</p>"
        "<ol class=\"parts\">"
        + "".join(
            f"<li>{html.escape(row['id'])}</li>" for row in rows
        )
        + "</ol></section>"
    ]
    for index, row in enumerate(rows, start=1):
        placed = rows[: index - 1]
        groups = [(prev["edges"], OLD_STROKE, 1.2, "") for prev in placed]
        groups.append((row["edges"], GHOST_STROKE, 1.1, "4 3"))
        groups.append((_shift(row["edges"], dx), OLD_STROKE, 2.2, ""))
        seat = row["centroid"]
        exploded = (seat[0] + dx, seat[1], seat[2])
        svg = _svg(groups, (exploded, seat), width=640, height=420)
        label = html.escape(row["id"])
        sheets.append(
            f'<section class="sheet" data-step="{index}">'
            f'<div class="step-no">{index}</div>'
            f'<div class="csi">{svg}</div>'
            f'<aside class="pli"><div class="qty">1×</div><div class="pli-name">{label}</div></aside>'
            "</section>"
        )
    style = """
    @page { size: A4; margin: 12mm; }
    body { margin: 0; background: #fff; color: #1c1b18; font: 14px Arial, sans-serif; }
    .sheet { box-sizing: border-box; page-break-after: always; min-height: 273mm; padding: 14mm 16mm; position: relative; }
    .step-no { width: 36px; height: 36px; border: 2px solid #171714; border-radius: 50%; display: flex;
      align-items: center; justify-content: center; font: 700 18px ui-monospace, monospace; }
    .csi { width: min(100%, 640px); height: auto; margin-top: 12px; }
    .pli { position: absolute; top: 14mm; right: 16mm; width: 180px; border: 1.5px solid #1c1b18; padding: 8px; }
    .qty { font: 700 22px ui-monospace, monospace; }
    .pli-name, .note, .parts { font: 12px ui-monospace, monospace; color: #666159; }
    h1 { font-size: 28px; letter-spacing: -0.03em; margin: 0 0 8px; }
    @media print { .no-print { display: none; } }
    """
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{safe_title}</title><style>{style}</style></head><body>"
        f"<p class=\"no-print note\">{html.escape(NOTE)} Order is {html.escape(ORDER_RULE)} unless --order was set.</p>"
        + "".join(sheets)
        + "</body></html>"
    )


def _box(name: str, origin: tuple[float, float, float]) -> dict:
    ox, oy, oz = origin
    verts = [[ox, oy, oz], [ox + 10, oy, oz], [ox, oy + 8, oz], [ox, oy, oz + 6]]
    edges = [
        [[ox, oy, oz], [ox + 10, oy, oz]],
        [[ox, oy, oz], [ox, oy + 8, oz]],
        [[ox, oy, oz], [ox, oy, oz + 6]],
    ]
    return {"instance": name, "vertices": verts, "edges": edges, "color": "#c4b49a"}


def self_check() -> None:
    dump = {"source": "occ-step", "name": "two", "parts": [_box("a", (0, 0, 0)), _box("b", (0, 0, 12))]}
    text = booklet_html(dump, title="</title><script>alert(1)</script>")
    if text.count("data-step=\"") != 3:
        raise PlanError("expected a parts sheet plus one step per solid")
    if "2×" in text:
        raise PlanError("identical solids must not batch")
    if "This sequence is required" not in text or "<script>alert" in text:
        raise PlanError("note missing or title not escaped")
    if "min-height: 273mm" not in text or "box-sizing: border-box" not in text:
        raise PlanError("A4 sheet box is wrong")
    ordered = booklet_html(dump, order=["b", "a"])
    step1 = ordered.split('data-step="1"', 1)[1].split('data-step="2"', 1)[0]
    step2 = ordered.split('data-step="2"', 1)[1]
    if ">b<" not in step1 or ">a<" not in step2:
        raise PlanError("--order was ignored")
    try:
        booklet_html(dump, order=["a"])
    except PlanError:
        pass
    else:
        raise PlanError("short order should fail")
    mesh = dict(dump)
    mesh["source"] = "stl"
    try:
        booklet_html(mesh)
    except PlanError:
        pass
    else:
        raise PlanError("mesh source should fail")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Write an IKEA-style required-sequence sheet from an OCC dump.")
    parser.add_argument("scene", type=Path, nargs="?")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--title", default="")
    parser.add_argument("--order", default="", help="Comma-separated instance names. Each part once.")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        try:
            self_check()
        except PlanError as exc:
            sys.stderr.write(f"{exc}\n")
            return 1
        sys.stdout.write("ok\n")
        return 0
    if args.scene is None or args.out is None:
        parser.error("scene and --out are required unless --self-check")
    order = [part.strip() for part in args.order.split(",") if part.strip()] or None
    try:
        dump = json.loads(args.scene.read_text(encoding="utf-8"))
        text = booklet_html(dump, title=args.title, order=order)
    except (OSError, json.JSONDecodeError, PlanError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    sys.stderr.write(f"ikea {args.out} ({args.out.stat().st_size} bytes)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
