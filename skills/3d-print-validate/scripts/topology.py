"""Welded edge-graph audit of a triangle mesh."""
from __future__ import annotations

from typing import Dict, List, Tuple

from stl_io import Tri, tri_area


def topology_metrics(tris: List[Tri], weld_tolerance: float) -> Dict[str, object]:
    """Return graph stats plus tri_cid for occupancy checks."""
    if weld_tolerance <= 0:
        raise ValueError("weld tolerance must be positive")

    vertex_ids: Dict[Tuple[int, int, int], int] = {}
    edge_uses: Dict[Tuple[int, int], List[Tuple[int, int, int]]] = {}
    face_uses: Dict[Tuple[int, int, int], int] = {}
    degenerate = 0
    active_triangles: List[int] = []

    def vertex_id(p) -> int:
        key = tuple(int(round(float(c) / weld_tolerance)) for c in p)
        if key not in vertex_ids:
            vertex_ids[key] = len(vertex_ids)
        return vertex_ids[key]

    parent = list(range(len(tris)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for tri_index, (a, b, c) in enumerate(tris):
        ids = (vertex_id(a), vertex_id(b), vertex_id(c))
        if len(set(ids)) < 3 or tri_area(a, b, c) <= weld_tolerance * weld_tolerance:
            degenerate += 1
            continue
        active_triangles.append(tri_index)
        face_key = tuple(sorted(ids))
        face_uses[face_key] = face_uses.get(face_key, 0) + 1
        for u, v in ((ids[0], ids[1]), (ids[1], ids[2]), (ids[2], ids[0])):
            edge_key = (u, v) if u < v else (v, u)
            edge_uses.setdefault(edge_key, []).append((tri_index, u, v))

    boundary_edges = sum(1 for uses in edge_uses.values() if len(uses) == 1)
    nonmanifold_edges = sum(1 for uses in edge_uses.values() if len(uses) > 2)
    orientation_edges = 0
    for uses in edge_uses.values():
        if len(uses) == 2:
            _, u0, v0 = uses[0]
            _, u1, v1 = uses[1]
            if not (u0 == v1 and v0 == u1):
                orientation_edges += 1
        first = uses[0][0]
        for use in uses[1:]:
            union(first, use[0])

    component_ids: Dict[int, int] = {}
    next_cid = 0
    tri_cid: Dict[int, int] = {}
    for i in active_triangles:
        root = find(i)
        if root not in component_ids:
            component_ids[root] = next_cid
            next_cid += 1
        tri_cid[i] = component_ids[root]

    return {
        "vertices": len(vertex_ids),
        "edges": len(edge_uses),
        "boundary_edges": boundary_edges,
        "nonmanifold_edges": nonmanifold_edges,
        "orientation_edges": orientation_edges,
        "degenerate_faces": degenerate,
        "duplicate_faces": sum(count - 1 for count in face_uses.values() if count > 1),
        "components": next_cid,
        "tri_cid": tri_cid,
    }
