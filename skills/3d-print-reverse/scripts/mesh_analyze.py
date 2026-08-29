"""Load STL, topology, AABB/PCA-align, millimetre units."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ir_io import new_ir, r6
from mesh_common import (
    WELD_MM,
    alignment_record,
    load_mesh,
    mesh_bbox_volume,
    mesh_topology,
    pca_aabb_alignment,
    transform_mesh,
)


def _aabb(mesh) -> dict[str, list[float]]:
    mn, mx, _vol = mesh_bbox_volume(mesh)
    return {
        "min": [r6(mn[0]), r6(mn[1]), r6(mn[2])],
        "max": [r6(mx[0]), r6(mx[1]), r6(mx[2])],
    }


def analyze_stl(
    stl: Path,
    *,
    body: str = "body",
    units: str = "mm",
    origin: str = "center",
    force: bool = False,
    fit_mm: float = 0.05,
    max_deviation_mm: float = 0.2,
    snap_mm: float | None = None,
    input_rel: str | None = None,
) -> tuple[dict[str, Any], int]:
    """Return (IR, exit_code). exit 2 = illegal input unless --force."""
    mesh = load_mesh(stl, units=units, weld=WELD_MM)
    rotation, translation, method = pca_aabb_alignment(mesh, origin=origin)
    aligned = transform_mesh(mesh, rotation, translation)
    aligned_topo = mesh_topology(aligned)
    mn, mx, vol = mesh_bbox_volume(aligned)
    inverted = vol <= 0.0
    open_or_bad = bool(
        aligned_topo["boundary_edges"]
        or aligned_topo["nonmanifold_edges"]
        or aligned_topo["orientation_edges"]
        or inverted
    )
    ir = new_ir(
        input_stl=input_rel or str(stl.name),
        body=body,
        units="mm",
    )
    ir["alignment"] = alignment_record(rotation, translation, method)
    ir["tolerance"] = {
        "fit_mm": r6(fit_mm),
        "max_deviation_mm": r6(max_deviation_mm),
        "snap_mm": None if snap_mm is None else r6(snap_mm),
    }
    ir["topology"] = {
        "vertices": int(aligned_topo["vertices"]),
        "edges": int(aligned_topo["edges"]),
        "boundary_edges": int(aligned_topo["boundary_edges"]),
        "nonmanifold_edges": int(aligned_topo["nonmanifold_edges"]),
        "orientation_edges": int(aligned_topo["orientation_edges"]),
        "degenerate_faces": int(aligned_topo["degenerate_faces"]),
        "duplicate_faces": int(aligned_topo["duplicate_faces"]),
        "components": int(aligned_topo["components"]),
        "volume_mm3": r6(vol),
    }
    ir["aabb_mm"] = _aabb(aligned)
    ir["expected_shells"] = max(1, int(aligned_topo["components"]) or 1)
    ir["input_triangles"] = int(mesh.triangle_count)
    ir["open_mesh_forced"] = bool(force and open_or_bad)
    if open_or_bad and not force:
        ir["class"] = "failed"
        if (
            aligned_topo["boundary_edges"]
            or aligned_topo["nonmanifold_edges"]
            or aligned_topo["orientation_edges"]
        ):
            ir["warnings"].append("open or non-manifold mesh")
        if inverted:
            ir["warnings"].append("non-positive signed volume")
        return ir, 2
    if open_or_bad and force:
        ir["class"] = "failed"
        ir["warnings"].append("illegal mesh analyzed with --force; STEP/STL delivery forbidden")
        if inverted:
            ir["warnings"].append("non-positive signed volume")
        return ir, 0
    size = [mx[i] - mn[i] for i in range(3)]
    names = ("width_mm", "depth_mm", "height_mm")
    labels = ("width", "depth", "height")
    dims = []
    for name, parameter, raw in zip(labels, names, size):
        value = raw if snap_mm is None else round(raw / snap_mm) * snap_mm
        dims.append(
            {
                "name": name,
                "parameter": parameter,
                "raw_mm": r6(raw),
                "value_mm": r6(value),
                "tolerance_mm": r6(max_deviation_mm),
                "source": "measured",
            }
        )
    ir["dimensions"] = dims
    return ir, 0
