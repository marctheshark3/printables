"""IR → CadQuery or VibeCAD/Part Python source. No host OCC import.

Kernel source extrudes the IR sketch profile and cuts holes at named origins.
Never emit an AABB box as the solid.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from geom import EPS, vcross, vdot, vlen, vnorm, vsub
from tessellate_solid import aabb_param_for_axis, _looks_rectangle, discretize_entities


def _params_block(ir: dict[str, Any], extra: list[tuple[str, float]] | None = None) -> str:
    lines = ["# Named millimetre parameters (reverse IR / PRINT_SPEC.yaml)."]
    seen: set[str] = set()
    for dim in ir.get("dimensions") or []:
        param = dim["parameter"]
        value = float(dim["value_mm"])
        lines.append(f"{param} = {value:.6f}")
        seen.add(param)
    for param, value in extra or []:
        if param in seen:
            continue
        lines.append(f"{param} = {float(value):.6f}")
        seen.add(param)
    if not ir.get("dimensions") and not extra:
        lines.append("width_mm = 1.000000")
    return "\n".join(lines) + "\n"


def _extrude_feature(ir: dict[str, Any]) -> dict[str, Any] | None:
    for feat in ir.get("features") or []:
        if feat.get("type") == "extrude" and feat.get("op") == "add":
            return feat
    return None


def _sketch_map(ir: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {s["id"]: s for s in ir.get("sketches") or []}


def _outer_uv(sketch: dict[str, Any]) -> list[tuple[float, float]]:
    for prof in sketch.get("profiles") or []:
        role = prof.get("role")
        if role == "hole" or str(prof.get("id", "")).startswith("hole"):
            continue
        pts = discretize_entities(prof.get("entities") or [])
        if pts:
            return [(float(p[0]), float(p[1])) for p in pts]
    return []


def _project_uv(origin_mm: list[float], sketch: dict[str, Any]) -> tuple[float, float]:
    so = tuple(float(x) for x in sketch["origin_mm"])
    sx = tuple(float(x) for x in sketch["x_axis"])
    sy = tuple(float(x) for x in sketch["y_axis"])
    rel = vsub(tuple(float(x) for x in origin_mm), so)
    return float(vdot(rel, sx)), float(vdot(rel, sy))


def _hole_records(ir: dict[str, Any], sketch: dict[str, Any] | None) -> list[dict[str, str]]:
    """Named diameter + UV/origin identifiers for each hole feature."""
    dim_names = {d["parameter"] for d in ir.get("dimensions") or []}
    out: list[dict[str, str]] = []
    for feat in ir.get("features") or []:
        if feat.get("type") != "hole":
            continue
        hid = feat["id"]
        d_param = f"hole_{hid}_d_mm"
        u_param = f"hole_{hid}_u_mm"
        v_param = f"hole_{hid}_v_mm"
        x_param = f"hole_{hid}_x_mm"
        y_param = f"hole_{hid}_y_mm"
        uv = feat.get("uv_mm")
        origin = feat.get("origin_mm") or [0.0, 0.0, 0.0]
        if uv is None and sketch is not None:
            uv = list(_project_uv([float(c) for c in origin], sketch))
        if uv is None:
            uv = [0.0, 0.0]
        rec = {
            "id": hid,
            "d": d_param if d_param in dim_names else d_param,
            "u": u_param,
            "v": v_param,
            "x": x_param,
            "y": y_param,
            "d_val": float(feat.get("diameter_mm") or 0.0),
            "u_val": float(uv[0]),
            "v_val": float(uv[1]),
            "x_val": float(origin[0]),
            "y_val": float(origin[1]),
        }
        out.append(rec)
    return out


def cadquery_plane_frame(
    sketch: dict[str, Any],
    direction: Any = None,
) -> tuple[tuple[float, float, float], tuple[float, float, float], float]:
    """CadQuery Plane axes that preserve IR sketch UV.

    CadQuery sets yDir = normal × xDir. Plane.normal must be sketch x_axis ×
    y_axis (not the extrude direction) so origin+u*x+v*(n×x) matches
    origin+u*x_axis+v*y_axis. Extrude sign is sign(direction · plane_normal).
    """
    x_axis = tuple(float(c) for c in sketch["x_axis"])
    y_axis = tuple(float(c) for c in sketch["y_axis"])
    crossed = vcross(x_axis, y_axis)
    if vlen(crossed) < EPS:
        nsrc = sketch.get("normal") or (0.0, 0.0, 1.0)
        plane_n = vnorm(tuple(float(c) for c in nsrc))
    else:
        plane_n = vnorm(crossed)
    if direction is None:
        direction = sketch.get("normal") or plane_n
    dvec = tuple(float(c) for c in direction)
    if vlen(dvec) < EPS:
        sign = 1.0
    else:
        sign = 1.0 if vdot(plane_n, vnorm(dvec)) >= 0.0 else -1.0
    return x_axis, plane_n, sign


def _extra_params(ir: dict[str, Any], sketch: dict[str, Any] | None, holes: list[dict[str, str]], outer: list[tuple[float, float]]) -> list[tuple[str, float]]:
    extra: list[tuple[str, float]] = []
    if sketch is not None:
        ox, oy, oz = (float(x) for x in sketch["origin_mm"])
        sid = sketch["id"]
        extra += [
            (f"{sid}_ox_mm", ox),
            (f"{sid}_oy_mm", oy),
            (f"{sid}_oz_mm", oz),
        ]
        for i, (u, v) in enumerate(outer):
            extra.append((f"{sid}_p{i}_u_mm", u))
            extra.append((f"{sid}_p{i}_v_mm", v))
    for h in holes:
        extra.append((h["d"], h["d_val"]))
        extra.append((h["u"], h["u_val"]))
        extra.append((h["v"], h["v_val"]))
        extra.append((h["x"], h["x_val"]))
        extra.append((h["y"], h["y_val"]))
    return extra


def emit_cadquery_source(ir: dict[str, Any]) -> str:
    body = ir.get("body") or "body"
    feat = _extrude_feature(ir)
    sketches = _sketch_map(ir)
    sketch = sketches.get((feat or {}).get("sketch") or "") if feat else None
    outer = _outer_uv(sketch) if sketch else []
    holes = _hole_records(ir, sketch)
    extra = _extra_params(ir, sketch, holes, outer)
    depth_param = "extrude_depth_mm"
    if not any(d.get("parameter") == depth_param for d in ir.get("dimensions") or []):
        extra.append((depth_param, float((feat or {}).get("depth_mm") or 1.0)))

    lines = [
        '"""Parametric rebuild from reverse IR. CadQuery / OCC. Millimetres."""',
        "from pathlib import Path",
        "",
        _params_block(ir, extra).rstrip(),
        "",
        "def project_root():",
        "    return Path(__file__).resolve().parent.parent",
        "",
        "def build():",
        "    import cadquery as cq",
    ]

    if sketch is not None and outer:
        sid = sketch["id"]
        xDir, plane_n, extrude_sign = cadquery_plane_frame(
            sketch, (feat or {}).get("direction")
        )
        xx, xy, xz = xDir
        nx, ny, nz = plane_n
        sign_lit = f"{extrude_sign:.1f}"
        lines += [
            f"    plane = cq.Plane(",
            f"        origin=cq.Vector({sid}_ox_mm, {sid}_oy_mm, {sid}_oz_mm),",
            f"        xDir=cq.Vector({xx:.6f}, {xy:.6f}, {xz:.6f}),",
            f"        normal=cq.Vector({nx:.6f}, {ny:.6f}, {nz:.6f}),",
            "    )",
            "    wp = cq.Workplane(plane)",
        ]
        if _looks_rectangle(outer) and any(d.get("parameter") == "width_mm" for d in ir.get("dimensions") or []):
            yDir = vcross(plane_n, xDir)
            u_param = aabb_param_for_axis(xDir)
            v_param = aabb_param_for_axis(yDir)
            lines.append(f"    wp = wp.rect({u_param}, {v_param})")
        else:
            lines.append(f"    wp = wp.moveTo({sid}_p0_u_mm, {sid}_p0_v_mm)")
            for i in range(1, len(outer)):
                lines.append(f"    wp = wp.lineTo({sid}_p{i}_u_mm, {sid}_p{i}_v_mm)")
            lines.append("    wp = wp.close()")
        lines.append(f"    solid = wp.extrude({sign_lit} * float(extrude_depth_mm))")
        for h in holes:
            lines += [
                "    cutter = (",
                "        cq.Workplane(plane)",
                f"        .moveTo({h['u']}, {h['v']})",
                f"        .circle({h['d']} / 2.0)",
                f"        .extrude({sign_lit} * (float(extrude_depth_mm) + 2.0))",
                "    )",
                "    solid = solid.cut(cutter)",
            ]
    else:
        lines += [
            "    raise RuntimeError('HARD: IR has no extrude sketch to rebuild')",
            "    solid = None",
        ]
    lines += [
        "    return solid",
        "",
        "def main():",
        "    import cadquery as cq",
        "    root = project_root()",
        "    solid = build()",
        f"    step = root / 'step' / '{body}.step'",
        f"    stl = root / 'stl' / '{body}.stl'",
        "    step.parent.mkdir(parents=True, exist_ok=True)",
        "    stl.parent.mkdir(parents=True, exist_ok=True)",
        "    cq.exporters.export(solid, str(step))",
        "    cq.exporters.export(solid, str(stl))",
        "    print('exported', step, stl)",
        "",
        "if __name__ in {'__main__', Path(__file__).stem}:",
        "    main()",
        "",
    ]
    return "\n".join(lines)


def emit_vibecad_source(ir: dict[str, Any]) -> str:
    body = ir.get("body") or "body"
    feat = _extrude_feature(ir)
    sketches = _sketch_map(ir)
    sketch = sketches.get((feat or {}).get("sketch") or "") if feat else None
    outer = _outer_uv(sketch) if sketch else []
    holes = _hole_records(ir, sketch)
    extra = _extra_params(ir, sketch, holes, outer)
    if not any(d.get("parameter") == "extrude_depth_mm" for d in ir.get("dimensions") or []):
        extra.append(("extrude_depth_mm", float((feat or {}).get("depth_mm") or 1.0)))

    nx, ny, nz = (0.0, 0.0, 1.0)
    xx, xy, xz = (1.0, 0.0, 0.0)
    yx, yy, yz = (0.0, 1.0, 0.0)
    if feat:
        nx, ny, nz = (float(x) for x in feat.get("direction") or (0.0, 0.0, 1.0))
    if sketch:
        xx, xy, xz = (float(x) for x in sketch["x_axis"])
        yx, yy, yz = (float(x) for x in sketch["y_axis"])

    lines = [
        '"""Parametric rebuild from reverse IR. 10-X-eng/vibecad Part CSG. Millimetres."""',
        "from pathlib import Path",
        "",
        _params_block(ir, extra).rstrip(),
        "",
        "def project_root():",
        "    return Path(__file__).resolve().parent.parent",
        "",
        "def build_solid():",
        "    import FreeCAD as App",
        "    import Part",
    ]
    if sketch is not None and outer:
        sid = sketch["id"]
        lines += [
            f"    origin = App.Vector({sid}_ox_mm, {sid}_oy_mm, {sid}_oz_mm)",
            f"    x_axis = App.Vector({xx:.6f}, {xy:.6f}, {xz:.6f})",
            f"    y_axis = App.Vector({yx:.6f}, {yy:.6f}, {yz:.6f})",
            f"    direction = App.Vector({nx:.6f}, {ny:.6f}, {nz:.6f})",
        ]
        if _looks_rectangle(outer) and any(d.get("parameter") == "width_mm" for d in ir.get("dimensions") or []):
            u_param = aabb_param_for_axis((xx, xy, xz))
            v_param = aabb_param_for_axis((yx, yy, yz))
            lines += [
                f"    hx = float({u_param}) / 2.0",
                f"    hy = float({v_param}) / 2.0",
                "    corners = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]",
                "    pts = [origin + x_axis * u + y_axis * v for u, v in corners]",
            ]
        else:
            lines.append("    pts = [")
            for i in range(len(outer)):
                lines.append(
                    f"        origin + x_axis * {sid}_p{i}_u_mm + y_axis * {sid}_p{i}_v_mm,"
                )
            lines.append("    ]")
        lines += [
            "    pts.append(pts[0])",
            "    face = Part.Face(Part.makePolygon(pts))",
            "    solid = face.extrude(direction * float(extrude_depth_mm))",
        ]
        for h in holes:
            lines += [
                f"    hole_origin = origin + x_axis * {h['u']} + y_axis * {h['v']} - direction",
                f"    cutter = Part.makeCylinder(float({h['d']}) / 2.0, float(extrude_depth_mm) + 2.0,",
                "                               hole_origin, direction)",
                "    solid = solid.cut(cutter)",
            ]
        lines += [
            "    if len(solid.Solids) != 1:",
            "        raise RuntimeError(f'HARD: solid count {len(solid.Solids)} != expected_shells 1')",
            "    return solid",
        ]
    else:
        lines += [
            "    raise RuntimeError('HARD: IR has no extrude sketch to rebuild')",
        ]
    lines += [
        "",
        "def main():",
        "    try:",
        "        import FreeCAD  # noqa: F401",
        "        import Mesh  # noqa: F401",
        "        import Part  # noqa: F401",
        "    except ImportError:",
        "        raise SystemExit(",
        "            'HARD: host python3 has no FreeCAD. Execute inside VibeCADCmd/'",
        "            'freecadcmd (x86_64 AppImage) or POST /v1/run. Linux ARM '",
        "            'qemu-x86_64 AppImage is not a supported backend.'",
        "        ) from None",
        "    import os",
        "    import Part",
        "    import Mesh",
        "    import FreeCAD as App",
        "    root = project_root()",
        f"    stl = Path(os.environ.get('PRINTABLES_STL', str(root / 'stl' / '{body}.stl')))",
        f"    step = Path(os.environ.get('PRINTABLES_STEP', str(root / 'step' / '{body}.step')))",
        "    stl.parent.mkdir(parents=True, exist_ok=True)",
        "    step.parent.mkdir(parents=True, exist_ok=True)",
        "    shape = build_solid()",
        "    doc = App.newDocument('reverse')",
        "    feat = doc.addObject('Part::Feature', 'body')",
        "    feat.Shape = shape",
        "    doc.recompute()",
        "    Mesh.export([feat], str(stl))",
        "    Part.export([feat], str(step))",
        "    print('exported', stl, step)",
        "",
        "if __name__ in {'__main__', Path(__file__).stem}:",
        "    main()",
        "",
    ]
    return "\n".join(lines)


def write_kernel_source(project: Path, ir: dict[str, Any], kernel: str) -> Path:
    body = ir.get("body") or "body"
    path = project / "src" / f"{body}.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    if kernel == "vibecad":
        path.write_text(emit_vibecad_source(ir), encoding="utf-8")
    else:
        path.write_text(emit_cadquery_source(ir), encoding="utf-8")
    return path
