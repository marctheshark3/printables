#!/usr/bin/env python3
"""Write a printable Lego-style sheet from an OCC STEP dump.

Edge art, not a shaded render. The inspector Instructions button draws the
shaded pages. Both use plan_steps.order: centroid z, then y, then x, then name.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

from plan_steps import ORDER_RULE, PlanError, SOURCES, centroid, plan_from_dump

COS30 = 0.8660254037844386
SIN30 = 0.5
NEW_STROKE = "#c42b23"
OLD_STROKE = "#1c1b18"
NOTE = f"Assembly order is {ORDER_RULE}. Not an LDraw model. Not print approval."


def project(x: float, y: float, z: float) -> tuple[float, float]:
    return ((x - y) * COS30, -(z + (x + y) * SIN30))


def _edges(part: dict) -> list:
    edges = part.get("edges") or []
    if not edges:
        raise PlanError(f"{part.get('instance') or part.get('id') or 'part'} has no BREP edges")
    return edges


def _shift(edges: list, origin: tuple[float, float, float]) -> list:
    ox, oy, oz = origin
    shifted = []
    for seg in edges:
        if len(seg) != 2:
            raise PlanError("edge is not a segment")
        shifted.append([[float(p[0]) - ox, float(p[1]) - oy, float(p[2]) - oz] for p in seg])
    return shifted


def _points(edges: list) -> list[tuple[float, float]]:
    pts = []
    for seg in edges:
        for p in seg:
            pts.append(project(float(p[0]), float(p[1]), float(p[2])))
    return pts


def _fit(points: list[tuple[float, float]], width: float, height: float, pad: float = 16) -> tuple[float, float, float]:
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
        chunks.append(f"M{ox + ax * scale:.2f},{oy + ay * scale:.2f}L{ox + bx * scale:.2f},{oy + by * scale:.2f}")
    return "".join(chunks)


def svg_edges(edge_groups: list[tuple[list, str, float]], *, width: int, height: int, css: str, step: int) -> str:
    points = []
    for edges, _stroke, _width in edge_groups:
        points.extend(_points(edges))
    ox, oy, scale = _fit(points, width, height)
    paths = []
    for edges, stroke, stroke_width in edge_groups:
        d = _path(edges, ox, oy, scale)
        if not d:
            continue
        paths.append(
            f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}" '
            'stroke-linecap="square" stroke-linejoin="miter"/>'
        )
    body = "".join(paths)
    return (
        f'<svg class="{css}" data-step="{step}" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">{body}</svg>'
    )


def booklet_html(dump: dict, *, title: str = "", z_band_mm: float = 2.0) -> str:
    if not isinstance(dump, dict) or dump.get("source") not in SOURCES:
        raise PlanError("dump.source must be occ-step (CAD), not a mesh export")
    by_id = {}
    for i, part in enumerate(dump.get("parts") or []):
        name = str(part.get("instance") or part.get("id") or f"solid-{i}")
        if name in by_id:
            raise PlanError(f"duplicate instance {name}")
        _edges(part)
        by_id[name] = part
    steps = plan_from_dump(dump, z_band_mm=z_band_mm)
    page_title = title or dump.get("step") or "Assembly"
    safe_title = html.escape(str(page_title), quote=True)
    bom = []
    for step in steps:
        names = ", ".join(html.escape(n) for n in step["new_ids"])
        bom.append(f"<li>Step {step['number']} · {step['quantity']}× · {names}</li>")
    sheets = [
        "<section class=\"sheet\" data-role=\"bom\">"
        f"<h1>{safe_title}</h1>"
        f"<p class=\"note\">{html.escape(NOTE)}</p>"
        "<ol>"
        + "".join(bom)
        + "</ol></section>"
    ]
    for step in steps:
        previous = []
        fresh = []
        new = set(step["new_ids"])
        for name in step["placed_ids"]:
            part = by_id[name]
            (fresh if name in new else previous).append(_edges(part))
        groups = [(edges, OLD_STROKE, 1.2) for edges in previous]
        groups.extend((edges, NEW_STROKE, 2.4) for edges in fresh)
        csi = svg_edges(groups, width=640, height=480, css="csi", step=step["number"])
        first = by_id[step["new_ids"][0]]
        pli_edges = _shift(_edges(first), centroid(first["vertices"]))
        pli = svg_edges([(pli_edges, NEW_STROKE, 2.2)], width=200, height=160, css="pli-art", step=step["number"])
        label = html.escape(step["new_ids"][0] if step["quantity"] == 1 else step["label"])
        sheets.append(
            f'<section class="sheet" data-step="{step["number"]}">'
            f'<div class="step-no">{step["number"]}</div>'
            f"{csi}"
            '<aside class="pli">'
            f"{pli}"
            f'<div class="qty">{step["quantity"]}×</div>'
            f'<div class="pli-name">{label}</div>'
            "</aside></section>"
        )
    style = """
    @page { size: A4; margin: 12mm; }
    body { margin: 0; background: #fff; color: #1c1b18; font: 14px Arial, sans-serif; }
    .sheet { box-sizing: border-box; page-break-after: always; min-height: 273mm; padding: 14mm 16mm; position: relative; }
    .step-no { width: 42px; height: 42px; background: #171714; color: #fff; display: flex;
      align-items: center; justify-content: center; font: 700 20px ui-monospace, monospace; }
    .csi { width: min(100%, 640px); height: auto; margin-top: 12px; }
    .pli { position: absolute; top: 14mm; right: 16mm; width: 200px; border: 2px solid #1c1b18;
      padding: 8px; background: #fff; }
    .qty { font: 700 22px ui-monospace, monospace; margin-top: 6px; }
    .pli-name, .note { font: 12px ui-monospace, monospace; color: #666159; }
    h1 { font-size: 28px; letter-spacing: -0.03em; margin: 0 0 8px; }
    @media print { .no-print { display: none; } }
    """
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{safe_title}</title><style>{style}</style></head><body>"
        f"<p class=\"no-print note\">{html.escape(NOTE)}</p>"
        + "".join(sheets)
        + "</body></html>"
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Write a Lego-style instruction sheet from an OCC dump.")
    parser.add_argument("scene", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--z-band-mm", type=float, default=2.0)
    args = parser.parse_args(argv)
    try:
        dump = json.loads(args.scene.read_text(encoding="utf-8"))
        text = booklet_html(dump, title=args.title, z_band_mm=args.z_band_mm)
    except (OSError, json.JSONDecodeError, PlanError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    sys.stderr.write(f"instructions {args.out} ({args.out.stat().st_size} bytes)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
