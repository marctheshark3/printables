#!/usr/bin/env python3
"""Pack an OCC STEP dump into the CAD inspector study payload."""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path

CREAM = "#c4b49a"


class CadPackError(ValueError):
    pass


def _f32_bytes(triples) -> bytes:
    import array

    arr = array.array("f")
    for x, y, z in triples:
        arr.extend((float(x), float(y), float(z)))
    return arr.tobytes()


def _u32_bytes(triples) -> bytes:
    import array

    arr = array.array("I")
    for a, b, c in triples:
        arr.extend((int(a), int(b), int(c)))
    return arr.tobytes()


def pack_bytes(raw: bytes) -> str:
    return base64.b64encode(gzip.compress(raw, mtime=0)).decode("ascii")


def _bbox_mm(vertices) -> list[float]:
    if not vertices:
        return [0.0, 0.0, 0.0]
    xs = [float(v[0]) for v in vertices]
    ys = [float(v[1]) for v in vertices]
    zs = [float(v[2]) for v in vertices]
    return [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)]


def validate_dump(dump: dict) -> None:
    if not isinstance(dump, dict):
        raise CadPackError("dump must be an object")
    if dump.get("source") not in {"occ-step", "occ-brep"}:
        raise CadPackError("dump.source must be occ-step (CAD), not a mesh export")
    parts = dump.get("parts")
    if not isinstance(parts, list) or not parts:
        raise CadPackError("dump.parts is empty")
    for i, part in enumerate(parts):
        verts = part.get("vertices") or []
        tris = part.get("triangles") or []
        edges = part.get("edges") or []
        if len(verts) < 3 or not tris:
            raise CadPackError(f"part[{i}] has no tessellated faces")
        if not edges:
            raise CadPackError(
                f"part[{i}] has no BREP edges — refusing triangle-crease mesh"
            )


def study_from_dump(
    dump: dict,
    *,
    title: str = "CAD inspector",
    concept_id: str = "part",
    concept_name: str | None = None,
    release: str = "ENGINEERING REVIEW — NOT PRINT APPROVED",
) -> dict:
    validate_dump(dump)
    geometry: dict = {}
    items = []
    for i, part in enumerate(dump["parts"]):
        verts = part["vertices"]
        tris = part["triangles"]
        edges = part["edges"]
        face_raw = _f32_bytes(verts) + _u32_bytes(tris)
        face_key = hashlib.sha256(face_raw).hexdigest()[:20]
        if face_key not in geometry:
            geometry[face_key] = {
                "kind": "faces",
                "vertexCount": len(verts),
                "indexCount": len(tris) * 3,
                "data": pack_bytes(face_raw),
            }
        edge_pts = []
        for seg in edges:
            a, b = seg
            edge_pts.append(a)
            edge_pts.append(b)
        edge_raw = _f32_bytes(edge_pts)
        edge_key = hashlib.sha256(edge_raw).hexdigest()[:20]
        if edge_key not in geometry:
            geometry[edge_key] = {
                "kind": "brep-edges",
                "pointCount": len(edge_pts),
                "data": pack_bytes(edge_raw),
            }
        bbox = part.get("bbox_mm") or _bbox_mm(verts)
        explode = part.get("explode_mm")
        if explode is None:
            explode = [i * (float(bbox[0]) + 8.0), 0.0, 0.0]
        items.append(
            {
                "id": part.get("id") or f"solid-{i}",
                "instance": part.get("instance") or part.get("id") or f"solid-{i}",
                "kind": part.get("kind") or "printed",
                "group": part.get("group") or "part",
                "color": part.get("color") or CREAM,
                "geometry": face_key,
                "cad_edges": edge_key,
                "bbox_mm": [float(x) for x in bbox],
                "status": part.get("status") or "cad",
                "evidence": part.get("evidence")
                or "OCC tessellation + BREP edges from STEP",
                "explode_mm": [float(x) for x in explode],
            }
        )
    width = max((it["bbox_mm"][0] for it in items), default=0)
    depth = max((it["bbox_mm"][1] for it in items), default=0)
    height = max((it["bbox_mm"][2] for it in items), default=0)
    concept = {
        "id": concept_id,
        "name": concept_name or dump.get("step") or title,
        "release": release,
        "priority": "CAD inspector · mill STEP",
        "service": "Orthographic inspection of OCC faces and BREP edges. Not a STEP editor.",
        "width": round(width, 2),
        "depth": round(depth, 2),
        "height": round(height, 2),
        "default_view": "solid",
        "views": ["solid", "translucent", "exploded", "installed"],
        "items": items,
        "metrics": {
            "solids": len(items),
            "source": dump.get("step") or "step",
            "deflection_mm": dump.get("deflection_mm"),
        },
    }
    return {
        "title": title,
        "brand": "RAGE INDUSTRIES / CAD INSPECTOR",
        "concepts": [concept],
        "geometry": geometry,
        "issues": dump.get("issues") or [],
        "source": dump.get("source"),
        "step": dump.get("step"),
    }


def load_dump(path: Path) -> dict:
    dump = json.loads(path.read_text())
    validate_dump(dump)
    return dump
