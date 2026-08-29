"""Hypothesis: extrude / revolve / loft / hole / fillet / chamfer / mirror / pattern."""
from __future__ import annotations

from typing import Any, Sequence

from geom import angle_deg, snap_value, vdot, vnorm, vscale, vsub
from ir_io import r6


def _planes(regions: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in regions if r.get("kind") == "plane"]


def _cylinders(regions: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in regions if r.get("kind") == "cylinder"]


def _parallel(n0: Sequence[float], n1: Sequence[float], deg: float = 8.0) -> bool:
    return angle_deg(tuple(n0), tuple(n1)) <= deg  # type: ignore[arg-type]


def _antiparallel(n0: Sequence[float], n1: Sequence[float], deg: float = 8.0) -> bool:
    return angle_deg(tuple(n0), vscale(tuple(n1), -1.0)) <= deg  # type: ignore[arg-type]


def _axis_name(n: Sequence[float]) -> str:
    ax = max(range(3), key=lambda i: abs(n[i]))
    return "xyz"[ax]


def hypothesize_features(
    ir: dict[str, Any],
    *,
    organic_ok: bool = False,
) -> dict[str, Any]:
    regions = ir.get("region_list") or []
    sketches = ir.get("sketches") or []
    fit_mm = float(ir.get("tolerance", {}).get("fit_mm", 0.05))
    max_dev = float(ir.get("tolerance", {}).get("max_deviation_mm", 0.2))
    snap_mm = ir.get("tolerance", {}).get("snap_mm")
    snap = float(snap_mm) if snap_mm is not None else None
    planes = _planes(regions)
    cylinders = _cylinders(regions)
    features: list[dict[str, Any]] = []
    mixed: list[dict[str, Any]] = []
    fid = 0

    # Caps: largest pair of antiparallel planes, preferring world-Z.
    caps = None
    best = (-1.0, -1.0)
    for i, a in enumerate(planes):
        for b in planes[i + 1 :]:
            na, nb = a["normal"], b["normal"]
            if not _antiparallel(na, nb):
                continue
            area = min(float(a["area_mm2"]), float(b["area_mm2"]))
            z_align = abs(float(na[2]))
            score = (area, z_align)
            if score > best:
                best = score
                caps = (a, b)
    if caps is not None and sketches:
        a, b = caps
        origin_a = tuple(a["origin_mm"])
        origin_b = tuple(b["origin_mm"])
        n = vnorm(tuple(a["normal"]))  # type: ignore[arg-type]
        delta = vsub(origin_b, origin_a)  # type: ignore[arg-type]
        if vdot(delta, n) < 0:
            n = vscale(n, -1.0)
        depth = abs(vdot(delta, n))
        sketch = next((s for s in sketches if s.get("region_id") == a["id"]), None)
        if sketch is None:
            sketch = next((s for s in sketches if s.get("region_id") == b["id"]), sketches[0])
            n = vscale(n, -1.0)
        fid += 1
        depth_v = snap_value(depth, snap)
        features.append(
            {
                "id": f"f{fid}",
                "type": "extrude",
                "op": "add",
                "end": "blind",
                "sketch": sketch["id"],
                "depth_mm": r6(depth_v),
                "depth_raw_mm": r6(depth),
                "direction": [r6(x) for x in n],
            }
        )
        # Holes: inward cylindrical walls through along the extrude axis.
        aabb = ir.get("aabb_mm") or {}
        mn = aabb.get("min") or [-1e9, -1e9, -1e9]
        mx = aabb.get("max") or [1e9, 1e9, 1e9]
        ax = max(range(3), key=lambda i: abs(n[i]))
        max_r = 0.45 * min(mx[i] - mn[i] for i in range(3) if i != ax)
        for cyl in cylinders:
            axis = cyl.get("axis") or [0, 0, 1]
            if angle_deg(tuple(axis), n) > 8.0 and angle_deg(tuple(axis), vscale(n, -1.0)) > 8.0:
                continue
            radius = float(cyl.get("radius_mm") or 0.0)
            if radius < fit_mm or radius > max_r:
                continue
            if int(cyl.get("n_faces") or 0) < 16:
                continue
            fid += 1
            d_raw = 2.0 * radius
            origin = cyl.get("origin_mm")
            uv = None
            if origin:
                so = tuple(float(x) for x in sketch["origin_mm"])
                sx = tuple(float(x) for x in sketch["x_axis"])
                sy = tuple(float(x) for x in sketch["y_axis"])
                rel = vsub(tuple(float(x) for x in origin), so)
                uv = [r6(vdot(rel, sx)), r6(vdot(rel, sy))]
            features.append(
                {
                    "id": f"f{fid}",
                    "type": "hole",
                    "op": "cut",
                    "end": "through-all",
                    "sketch": sketch["id"],
                    "diameter_mm": r6(snap_value(d_raw, snap)),
                    "diameter_raw_mm": r6(d_raw),
                    "axis": [r6(x) for x in axis],
                    "origin_mm": origin,
                    "uv_mm": uv,
                    "region_id": cyl["id"],
                }
            )

        # Chamfer: planar strips ~45° to a pair of planes.
        for plane in planes:
            if plane in caps:
                continue
            n_p = plane["normal"]
            ang_a = angle_deg(tuple(n_p), tuple(a["normal"]))
            if 40.0 <= ang_a <= 50.0:
                fid += 1
                # strip width ≈ chamfer size
                features.append(
                    {
                        "id": f"f{fid}",
                        "type": "chamfer",
                        "op": "blend",
                        "distance_mm": r6(snap_value(math_safe_chamfer(plane, a, b), snap)),
                        "region_id": plane["id"],
                    }
                )

    counts = ir.get("regions") or {}
    fallback = int(counts.get("fallback") or 0)
    freeform = int(counts.get("freeform_triangles") or 0)
    if fallback and features:
        mixed.append({"id": "fallback", "class": "freeform", "triangles": freeform})

    ir["features"] = features
    ir["mixed"] = mixed
    if mixed:
        ir["class"] = "failed"
        ir["warnings"] = list(ir.get("warnings") or []) + [
            "mixed region classes; silent mixed output is HARD"
        ]
    elif features and fallback == 0:
        ir["class"] = "parametric"
    elif (counts.get("plane") or 0) + (counts.get("cylinder") or 0) + (
        counts.get("cone") or 0
    ) + (counts.get("sphere") or 0) > 0 and not features:
        ir["class"] = "analytic"
    elif organic_ok and freeform > 0:
        ir["class"] = "organic"
    else:
        ir["class"] = "failed" if not features else "parametric"

    # Measured hole dimensions.
    dims = list(ir.get("dimensions") or [])
    have = {d["parameter"] for d in dims}
    for feat in features:
        if feat["type"] == "hole":
            param = f"hole_{feat['id']}_d_mm"
            if param not in have:
                dims.append(
                    {
                        "name": feat["id"] + "_diameter",
                        "parameter": param,
                        "raw_mm": feat["diameter_raw_mm"],
                        "value_mm": feat["diameter_mm"],
                        "tolerance_mm": r6(max_dev),
                        "source": "measured",
                    }
                )
                have.add(param)
        if feat["type"] == "extrude":
            param = "extrude_depth_mm"
            if param not in have:
                dims.append(
                    {
                        "name": "extrude_depth",
                        "parameter": param,
                        "raw_mm": feat["depth_raw_mm"],
                        "value_mm": feat["depth_mm"],
                        "tolerance_mm": r6(max_dev),
                        "source": "measured",
                    }
                )
                have.add(param)
    dims.sort(key=lambda d: d["parameter"])
    ir["dimensions"] = dims
    return ir


def math_safe_chamfer(plane: dict[str, Any], a: dict[str, Any], b: dict[str, Any]) -> float:
    # Distance between the two cap planes times tan(22.5) is not used; use strip extent.
    return float(plane.get("area_mm2") or 0.0) ** 0.5 * 0.25
