"""Dump mill STEP as OCC tessellated faces + discretized BREP edges.

Runs inside FreeCADCmd only. Host python3 has no FreeCAD.

  export QT_QPA_PLATFORM=offscreen
  export CAD_RENDER_STEP=/abs/part.step
  export CAD_RENDER_OUT=/abs/scene.json
  "$VIBECAD_CMD" -c dump_cad_scene.py

FreeCADCmd -c never sets __name__ == "__main__".
"""
from __future__ import annotations

import json
import os
import sys
import traceback


def _die(msg: str, code: int = 1) -> None:
    sys.stderr.write(msg + "\n")
    raise SystemExit(code)


def _vec(p) -> list[float]:
    return [float(p.x), float(p.y), float(p.z)]


def _tessellate(solid, deflection: float):
    verts, tris = solid.tessellate(deflection)
    vertices = [[float(v.x), float(v.y), float(v.z)] if hasattr(v, "x") else [float(v[0]), float(v[1]), float(v[2])] for v in verts]
    triangles = [[int(a), int(b), int(c)] for a, b, c in tris]
    edges = []
    for edge in solid.Edges:
        try:
            pts = edge.discretize(Deflection=deflection)
        except Exception:
            try:
                pts = edge.discretize(20)
            except Exception:
                continue
        if len(pts) < 2:
            continue
        prev = _vec(pts[0])
        for p in pts[1:]:
            cur = _vec(p)
            edges.append([prev, cur])
            prev = cur
    bb = solid.BoundBox
    bbox = [float(bb.XLength), float(bb.YLength), float(bb.ZLength)]
    try:
        volume = float(solid.Volume)
    except Exception:
        volume = None
    return vertices, triangles, edges, bbox, volume


def main() -> int:
    step = os.environ.get("CAD_RENDER_STEP")
    out = os.environ.get("CAD_RENDER_OUT")
    if not step or not out:
        _die("CAD_RENDER_STEP and CAD_RENDER_OUT are required")
    if not os.path.isfile(step):
        _die(f"STEP not found: {step}")
    deflection = float(os.environ.get("CAD_RENDER_DEFLECTION", "0.15"))
    color = os.environ.get("CAD_RENDER_COLOR", "#c4b49a")
    try:
        import Part  # noqa: F401  FreeCAD
    except Exception:
        _die("FreeCAD Part missing — run this file under FreeCADCmd -c, not host python3")
    import Part

    shape = Part.Shape()
    try:
        shape.read(step)
    except Exception as exc:
        _die(f"Part.Shape.read failed: {exc}")
    solids = list(shape.Solids) if shape.Solids else []
    if not solids:
        if shape.Faces:
            solids = [shape]
        else:
            _die("STEP has no solids or faces")
    parts = []
    for i, solid in enumerate(solids):
        vertices, triangles, edges, bbox, volume = _tessellate(solid, deflection)
        if len(vertices) < 3 or not triangles:
            _die(f"solid {i}: tessellation produced no faces")
        if not edges:
            _die(f"solid {i}: no BREP edges (refusing mesh-only dump)")
        name = os.environ.get("CAD_RENDER_NAME") or os.path.splitext(os.path.basename(step))[0]
        instance = name if len(solids) == 1 else f"{name}-{i}"
        parts.append(
            {
                "id": instance,
                "instance": instance,
                "kind": "printed",
                "group": "part",
                "color": color,
                "vertices": vertices,
                "triangles": triangles,
                "edges": edges,
                "bbox_mm": bbox,
                "volume_mm3": volume,
                "status": "cad",
                "evidence": f"OCC tessellation + BREP edges · {os.path.basename(step)} · deflection {deflection} mm",
            }
        )
    payload = {
        "source": "occ-step",
        "step": os.path.basename(step),
        "step_path": os.path.abspath(step),
        "deflection_mm": deflection,
        "parts": parts,
    }
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, separators=(",", ":"))
    sys.stderr.write(
        f"cad-dump {len(parts)} solid(s) → {out} "
        f"faces={sum(len(p['triangles']) for p in parts)} "
        f"edge_segs={sum(len(p['edges']) for p in parts)}\n"
    )
    return 0


try:
    raise SystemExit(main())
except SystemExit:
    raise
except Exception:
    traceback.print_exc()
    raise SystemExit(1)
