"""Dihedral region grow; fit plane → cylinder → cone → sphere."""
from __future__ import annotations

import hashlib
from collections import defaultdict, deque
from typing import Any, Dict, List, Sequence, Tuple

from geom import (
    angle_deg,
    fit_cone,
    fit_cylinder,
    fit_plane,
    fit_sphere,
    tri_area,
    vadd,
    vscale,
)
from ir_io import empty_regions, r6
from mesh_common import TriMesh, WELD_MM, load_mesh, pca_aabb_alignment, transform_mesh

DEFAULT_DIHEDRAL_DEG = 15.0


def _face_adjacency(mesh: TriMesh) -> Dict[int, List[int]]:
    edge_faces: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    for fi, (a, b, c) in enumerate(mesh.faces):
        for u, v in ((a, b), (b, c), (c, a)):
            key = (u, v) if u < v else (v, u)
            edge_faces[key].append(fi)
    adj: Dict[int, List[int]] = defaultdict(list)
    for faces in edge_faces.values():
        if len(faces) != 2:
            continue
        i, j = faces
        adj[i].append(j)
        adj[j].append(i)
    return adj


def _grow_with_fit(
    mesh: TriMesh,
    seed: int,
    assigned: set[int],
    adj: Dict[int, List[int]],
    dihedral_deg: float,
    fit_mm: float,
    fitter,
    min_points: int,
) -> List[int]:
    group = [seed]
    local = {seed}
    q: deque[int] = deque([seed])
    while q:
        fi = q.popleft()
        for nb in adj.get(fi, ()):
            if nb in assigned or nb in local:
                continue
            if angle_deg(mesh.normals[nb], mesh.normals[fi]) > dihedral_deg:
                continue
            trial = group + [nb]
            points = mesh.points_of(trial)
            if len(points) < min_points:
                group.append(nb)
                local.add(nb)
                q.append(nb)
                continue
            normals = [mesh.normals[i] for i in trial]
            fit = fitter(points, normals)
            if fit is None or float(fit.get("max_dev", 1e9)) > fit_mm:
                continue
            group.append(nb)
            local.add(nb)
            q.append(nb)
    if len(mesh.points_of(group)) < min_points:
        return group
    fit = fitter(mesh.points_of(group), [mesh.normals[i] for i in group])
    if fit is None or float(fit.get("max_dev", 1e9)) > fit_mm:
        return [seed]
    return group


def _plane_fitter(points, normals):
    return fit_plane(points, normals)


def _cyl_fitter(points, normals):
    return fit_cylinder(points, normals)


def _cone_fitter(points, normals):
    return fit_cone(points, normals)


def _sphere_fitter(points, normals):
    return fit_sphere(points)


def region_grow(
    mesh: TriMesh, dihedral_deg: float, fit_mm: float = 0.05
) -> List[List[int]]:
    """Grow neighbors only while the region still fits plane, then cylinder."""
    adj = _face_adjacency(mesh)
    assigned: set[int] = set()
    regions: List[List[int]] = []
    order = sorted(range(len(mesh.faces)), key=lambda i: -mesh.face_area(i))
    for seed in order:
        if seed in assigned:
            continue
        plane_g = _grow_with_fit(
            mesh, seed, assigned, adj, dihedral_deg, fit_mm, _plane_fitter, 3
        )
        cyl_g = _grow_with_fit(
            mesh, seed, assigned, adj, dihedral_deg, fit_mm, _cyl_fitter, 6
        )
        cone_g = _grow_with_fit(
            mesh, seed, assigned, adj, dihedral_deg, fit_mm, _cone_fitter, 8
        )
        sph_g = _grow_with_fit(
            mesh, seed, assigned, adj, dihedral_deg, fit_mm, _sphere_fitter, 4
        )
        candidates = [
            g
            for g in (plane_g, cyl_g, cone_g, sph_g)
            if g
        ]
        group = max(candidates, key=len) if candidates else [seed]
        if len(group) < 1:
            group = [seed]
        for fi in group:
            assigned.add(fi)
        regions.append(group)
    leftover = [i for i in range(len(mesh.faces)) if i not in assigned]
    if leftover:
        regions.append(leftover)
    return regions


def _stable_hash(vert_ids: Sequence[int]) -> str:
    payload = ",".join(str(i) for i in sorted(vert_ids)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _region_area(mesh: TriMesh, faces: Sequence[int]) -> float:
    return sum(mesh.face_area(i) for i in faces)


def classify_region(
    mesh: TriMesh, faces: Sequence[int], fit_mm: float
) -> dict[str, Any]:
    points = mesh.points_of(faces)
    normals = [mesh.normals[i] for i in faces]
    area = _region_area(mesh, faces)
    vert_ids = mesh.unique_vertex_ids(faces)
    rid = _stable_hash(vert_ids)
    plane = fit_plane(points, normals)
    if plane is not None and plane["max_dev"] <= fit_mm:
        return {
            "id": f"r_{rid}",
            "kind": "plane",
            "area_mm2": r6(area),
            "max_dev_mm": r6(plane["max_dev"]),
            "origin_mm": [r6(x) for x in plane["origin"]],
            "normal": [r6(x) for x in plane["normal"]],
            "n_faces": len(faces),
            "n_vertices": len(vert_ids),
            "face_ids": list(faces),
            "vertex_hash": rid,
        }
    cyl = fit_cylinder(points, normals)
    if cyl is not None and cyl["max_dev"] <= fit_mm:
        return {
            "id": f"r_{rid}",
            "kind": "cylinder",
            "area_mm2": r6(area),
            "max_dev_mm": r6(cyl["max_dev"]),
            "origin_mm": [r6(x) for x in cyl["origin"]],
            "axis": [r6(x) for x in cyl["axis"]],
            "radius_mm": r6(cyl["radius"]),
            "height_mm": r6(cyl["height"]),
            "n_faces": len(faces),
            "n_vertices": len(vert_ids),
            "face_ids": list(faces),
            "vertex_hash": rid,
        }
    cone = fit_cone(points, normals)
    if cone is not None and cone["max_dev"] <= fit_mm:
        return {
            "id": f"r_{rid}",
            "kind": "cone",
            "area_mm2": r6(area),
            "max_dev_mm": r6(cone["max_dev"]),
            "origin_mm": [r6(x) for x in cone["origin"]],
            "axis": [r6(x) for x in cone["axis"]],
            "n_faces": len(faces),
            "n_vertices": len(vert_ids),
            "face_ids": list(faces),
            "vertex_hash": rid,
        }
    sphere = fit_sphere(points)
    if sphere is not None and sphere["max_dev"] <= fit_mm:
        return {
            "id": f"r_{rid}",
            "kind": "sphere",
            "area_mm2": r6(area),
            "max_dev_mm": r6(sphere["max_dev"]),
            "origin_mm": [r6(x) for x in sphere["origin"]],
            "radius_mm": r6(sphere["radius"]),
            "n_faces": len(faces),
            "n_vertices": len(vert_ids),
            "face_ids": list(faces),
            "vertex_hash": rid,
        }
    return {
        "id": f"r_{rid}",
        "kind": "fallback",
        "area_mm2": r6(area),
        "max_dev_mm": r6(fit_mm + 1.0),
        "n_faces": len(faces),
        "n_vertices": len(vert_ids),
        "face_ids": list(faces),
        "vertex_hash": rid,
    }


def segment_mesh(
    mesh: TriMesh,
    *,
    fit_mm: float = 0.05,
    dihedral_deg: float = DEFAULT_DIHEDRAL_DEG,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    grown = region_grow(mesh, dihedral_deg, fit_mm=fit_mm)
    classified = [classify_region(mesh, faces, fit_mm) for faces in grown]
    classified.sort(key=lambda r: (-float(r["area_mm2"]), r["vertex_hash"]))
    counts = empty_regions()
    for region in classified:
        kind = region["kind"]
        if kind in counts:
            counts[kind] += 1
        else:
            counts["fallback"] += 1
        if kind == "fallback":
            counts["freeform_triangles"] += int(region["n_faces"])
    return classified, counts


def load_aligned_mesh(
    stl: Path,
    ir: dict[str, Any],
    *,
    units: str = "mm",
) -> TriMesh:
    mesh = load_mesh(stl, units=units, weld=WELD_MM)
    rotation, translation, _method = pca_aabb_alignment(mesh, origin="center")
    # Prefer IR-recorded alignment so analyze→segment is stable.
    al = ir.get("alignment") or {}
    if al.get("translation_mm") is not None:
        from mesh_common import rotation_from_ir

        rotation, translation = rotation_from_ir(ir)
    return transform_mesh(mesh, rotation, translation)


def apply_segment(
    ir: dict[str, Any],
    mesh: TriMesh,
    *,
    dihedral_deg: float = DEFAULT_DIHEDRAL_DEG,
) -> dict[str, Any]:
    fit_mm = float(ir.get("tolerance", {}).get("fit_mm", 0.05))
    regions, counts = segment_mesh(mesh, fit_mm=fit_mm, dihedral_deg=dihedral_deg)
    ir["regions"] = counts
    # Compact region_list for IR (drop bulky face_ids).
    compact = []
    for region in regions:
        item = {k: v for k, v in region.items() if k != "face_ids"}
        compact.append(item)
    ir["region_list"] = compact
    ir["_segment_face_ids"] = [r["face_ids"] for r in regions]
    return ir
