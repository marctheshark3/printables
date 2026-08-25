"""Mesh cleanup helpers for FDM export (Blender 4.x)."""
from __future__ import annotations

import bmesh
import bpy

from .fdm_cleanup import apply_modifiers, cleanup_fdm, merge_by_distance, recalculate_normals_outside
from .scene import set_active

__all__ = [
    "apply_modifiers",
    "cleanup_fdm",
    "merge_by_distance",
    "recalculate_normals_outside",
    "triangulate",
    "bmesh_from_object",
]


def triangulate(obj: bpy.types.Object) -> None:
    set_active(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY", ngon_method="BEAUTY")
    bpy.ops.object.mode_set(mode="OBJECT")


def bmesh_from_object(obj: bpy.types.Object) -> bmesh.types.BMesh:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    return bm
