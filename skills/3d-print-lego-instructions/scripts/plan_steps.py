#!/usr/bin/env python3
"""Bottom-up steps for a Lego-style sheet.

Order is centroid z, then y, then x, then name.
Consecutive parts with the same fingerprint inside Z_BAND_MM share a step.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

Z_BAND_MM = 2.0
ORDER_RULE = "centroid z, then y, then x, then name"
DEFAULT_COLOR = "#c4b49a"
SOURCES = {"occ-step", "occ-brep"}


class PlanError(ValueError):
    pass


def tenth(value: float) -> int:
    """Non-negative tenth-millimetre bucket. Matches the inspector planner."""
    return int(float(value) * 10 + 0.5)


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


def bbox_mm(part: dict) -> list[float]:
    given = part.get("bbox_mm")
    if isinstance(given, list) and len(given) == 3:
        return [float(given[0]), float(given[1]), float(given[2])]
    verts = part.get("vertices") or []
    if len(verts) < 3:
        raise PlanError("part has no vertices")
    xs = [float(v[0]) for v in verts]
    ys = [float(v[1]) for v in verts]
    zs = [float(v[2]) for v in verts]
    return [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)]


def fingerprint(part: dict) -> tuple:
    box = bbox_mm(part)
    color = str(part.get("color") or DEFAULT_COLOR)
    return (tenth(box[0]), tenth(box[1]), tenth(box[2]), len(part.get("vertices") or []), color)


def plan_steps(parts: list, *, z_band_mm: float = Z_BAND_MM) -> list[dict]:
    if not parts:
        raise PlanError("dump.parts is empty")
    if z_band_mm < 0:
        raise PlanError("z band must be >= 0")
    rows = []
    for i, part in enumerate(parts):
        if not isinstance(part, dict):
            raise PlanError(f"part[{i}] is not an object")
        verts = part.get("vertices") or []
        c = centroid(verts)
        name = str(part.get("instance") or part.get("id") or f"solid-{i}")
        rows.append({"id": name, "centroid": c, "fingerprint": fingerprint(part)})
    rows.sort(key=lambda row: (row["centroid"][2], row["centroid"][1], row["centroid"][0], row["id"]))
    steps = []
    i = 0
    while i < len(rows):
        anchor = rows[i]
        group = [anchor]
        j = i + 1
        while j < len(rows):
            nxt = rows[j]
            if nxt["fingerprint"] != anchor["fingerprint"]:
                break
            if abs(nxt["centroid"][2] - anchor["centroid"][2]) > z_band_mm:
                break
            group.append(nxt)
            j += 1
        qty = len(group)
        first = group[0]["id"]
        steps.append(
            {
                "number": len(steps) + 1,
                "new_ids": [row["id"] for row in group],
                "placed_ids": [row["id"] for row in rows[:j]],
                "quantity": qty,
                "label": first if qty == 1 else f"{first} ×{qty}",
            }
        )
        i = j
    return steps


def plan_from_dump(dump: dict, *, z_band_mm: float = Z_BAND_MM) -> list[dict]:
    if not isinstance(dump, dict):
        raise PlanError("dump must be an object")
    if dump.get("source") not in SOURCES:
        raise PlanError("dump.source must be occ-step (CAD), not a mesh export")
    parts = dump.get("parts")
    if not isinstance(parts, list):
        raise PlanError("dump.parts is empty")
    return plan_steps(parts, z_band_mm=z_band_mm)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Plan Lego-style steps from an OCC dump.")
    parser.add_argument("scene", type=Path)
    parser.add_argument("--z-band-mm", type=float, default=Z_BAND_MM)
    args = parser.parse_args(argv)
    try:
        dump = json.loads(args.scene.read_text(encoding="utf-8"))
        steps = plan_from_dump(dump, z_band_mm=args.z_band_mm)
    except (OSError, json.JSONDecodeError, PlanError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    json.dump(steps, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
