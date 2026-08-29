"""Indexed welded mesh wrapping 3d-print-validate stl_io/topology."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from geom import (
    Mat3,
    Tri,
    Vec3,
    identity3,
    matT,
    matvec,
    rpy_deg_from_matrix,
    snap_axes_to_xyz,
    tri_area,
    tri_normal,
    vadd,
    vmean,
    vscale,
    vsub,
    world_aligned_area_frac,
    covariance3,
    jacobi_eigen3,
    matrix_from_rpy_deg,
)

VALIDATE_SCRIPTS = Path(__file__).resolve().parent.parent.parent / "3d-print-validate" / "scripts"
if str(VALIDATE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(VALIDATE_SCRIPTS))

from stl_io import bbox_and_volume, load_binary_stl  # noqa: E402
from topology import topology_metrics  # noqa: E402

WELD_MM = 1e-5
INCH_TO_MM = 25.4


@dataclass
class TriMesh:
    vertices: List[Vec3]
    faces: List[Tuple[int, int, int]]
    normals: List[Vec3]
    weld_tolerance: float = WELD_MM
    source_path: str = ""
    triangle_count: int = 0
    units_in: str = "mm"
    scale_applied: float = 1.0

    def triangles_xyz(self) -> List[Tri]:
        out: List[Tri] = []
        for a, b, c in self.faces:
            out.append((self.vertices[a], self.vertices[b], self.vertices[c]))
        return out

    def face_area(self, index: int) -> float:
        a, b, c = self.faces[index]
        return tri_area(self.vertices[a], self.vertices[b], self.vertices[c])

    def unique_vertex_ids(self, face_ids: Sequence[int]) -> List[int]:
        seen: Dict[int, None] = {}
        for fi in face_ids:
            for vid in self.faces[fi]:
                seen[vid] = None
        return list(seen.keys())

    def points_of(self, face_ids: Sequence[int]) -> List[Vec3]:
        return [self.vertices[i] for i in self.unique_vertex_ids(face_ids)]


def weld_triangles(tris: Sequence[Tri], weld: float) -> Tuple[List[Vec3], List[Tuple[int, int, int]], List[Vec3]]:
    vertex_ids: Dict[Tuple[int, int, int], int] = {}
    vertices: List[Vec3] = []
    faces: List[Tuple[int, int, int]] = []
    normals: List[Vec3] = []

    def vid(p: Vec3) -> int:
        key = (int(round(p[0] / weld)), int(round(p[1] / weld)), int(round(p[2] / weld)))
        if key not in vertex_ids:
            vertex_ids[key] = len(vertices)
            vertices.append(p)
        return vertex_ids[key]

    for a, b, c in tris:
        ia, ib, ic = vid(a), vid(b), vid(c)
        if len({ia, ib, ic}) < 3:
            continue
        faces.append((ia, ib, ic))
        normals.append(tri_normal(vertices[ia], vertices[ib], vertices[ic]))
    return vertices, faces, normals


def load_mesh(path: Path, *, units: str = "mm", weld: float = WELD_MM) -> TriMesh:
    _normals, tris, ntri = load_binary_stl(path)
    scale = INCH_TO_MM if units == "inch" else 1.0
    if units not in {"mm", "inch"}:
        raise ValueError(f"units must be mm or inch, not {units!r}")
    if scale != 1.0:
        tris = [
            (vscale(a, scale), vscale(b, scale), vscale(c, scale))
            for a, b, c in tris
        ]
    vertices, faces, normals = weld_triangles(tris, weld)
    return TriMesh(
        vertices=vertices,
        faces=faces,
        normals=normals,
        weld_tolerance=weld,
        source_path=str(path),
        triangle_count=int(ntri),
        units_in=units,
        scale_applied=scale,
    )


def mesh_topology(mesh: TriMesh) -> dict:
    return topology_metrics(mesh.triangles_xyz(), mesh.weld_tolerance)


def mesh_bbox_volume(mesh: TriMesh):
    return bbox_and_volume(mesh.triangles_xyz())


def transform_mesh(mesh: TriMesh, rotation: Mat3, translation: Vec3) -> TriMesh:
    """aligned = R * (p - translation)."""
    verts = [matvec(rotation, vsub(p, translation)) for p in mesh.vertices]
    normals = [matvec(rotation, n) for n in mesh.normals]
    return TriMesh(
        vertices=verts,
        faces=list(mesh.faces),
        normals=normals,
        weld_tolerance=mesh.weld_tolerance,
        source_path=mesh.source_path,
        triangle_count=mesh.triangle_count,
        units_in=mesh.units_in,
        scale_applied=mesh.scale_applied,
    )


def inverse_transform_point(p: Vec3, rotation: Mat3, translation: Vec3) -> Vec3:
    return vadd(matvec(matT(rotation), p), translation)


def pca_aabb_alignment(mesh: TriMesh, origin: str = "center") -> Tuple[Mat3, Vec3, str]:
    """Return (R, translation, method). aligned = R * (p - translation)."""
    mn, mx, _vol = mesh_bbox_volume(mesh)
    if origin != "center":
        raise ValueError("v1 origin must be center")
    center = ((mn[0] + mx[0]) * 0.5, (mn[1] + mx[1]) * 0.5, (mn[2] + mx[2]) * 0.5)
    areas = [(mesh.normals[i], mesh.face_area(i)) for i in range(len(mesh.faces))]
    if world_aligned_area_frac(areas, 8.0) >= 0.85:
        return identity3(), center, "pca-aabb"
    cov = covariance3(mesh.vertices, center)
    evals, evecs = jacobi_eigen3(cov)
    ordered = sorted(range(3), key=lambda i: evals[i], reverse=True)
    cond = abs(evals[ordered[0]]) / max(abs(evals[ordered[2]]), 1e-18)
    if cond < 1.15:
        return identity3(), center, "pca-aabb"
    snapped = snap_axes_to_xyz(evecs)
    return snapped, center, "pca-aabb"


def alignment_record(rotation: Mat3, translation: Vec3, method: str) -> dict:
    rpy = rpy_deg_from_matrix(rotation)
    return {
        "method": method,
        "translation_mm": [float(translation[0]), float(translation[1]), float(translation[2])],
        "rotation_rpy_deg": [float(rpy[0]), float(rpy[1]), float(rpy[2])],
    }


def rotation_from_ir(ir: dict) -> Tuple[Mat3, Vec3]:
    al = ir.get("alignment") or {}
    t = al.get("translation_mm") or [0.0, 0.0, 0.0]
    rpy = al.get("rotation_rpy_deg") or [0.0, 0.0, 0.0]
    return matrix_from_rpy_deg(rpy), (float(t[0]), float(t[1]), float(t[2]))
