"""FDM-safe mesh cleanup. Prefer light over voxel remesh on mechanical shells."""
from __future__ import annotations

import bpy

from .scene import set_active


def merge_by_distance(obj: bpy.types.Object, dist: float = 0.05) -> None:
    set_active(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=dist)
    try:
        bpy.ops.mesh.dissolve_degenerate(threshold=max(1e-4, dist * 0.5))
    except RuntimeError:
        pass
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def recalculate_normals_outside(obj: bpy.types.Object) -> None:
    set_active(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def apply_modifiers(obj: bpy.types.Object) -> None:
    set_active(obj)
    for mod in list(obj.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except RuntimeError as exc:
            print(f"  WARN: could not apply modifier {mod.name}: {exc}")


def cleanup_fdm(
    obj: bpy.types.Object,
    *,
    mode: str = "light",
    merge_dist: float = 0.05,
    voxel: float = 0.35,
) -> None:
    """Post-boolean cleanup for printables.

    mode:
      light  — merge doubles + consistent normals. DEFAULT for shells/ports/bosses.
      voxel  — only for organic lattice unions that are already non-manifold soup.
               NEVER use on dimensional shells (melts walls, moves port faces).
    """
    merge_by_distance(obj, dist=merge_dist)
    recalculate_normals_outside(obj)
    if mode == "voxel":
        set_active(obj)
        for mod in list(obj.modifiers):
            obj.modifiers.remove(mod)
        mod = obj.modifiers.new("VoxelClean", type="REMESH")
        mod.mode = "VOXEL"
        mod.voxel_size = voxel
        apply_modifiers(obj)
        merge_by_distance(obj, dist=merge_dist)
        recalculate_normals_outside(obj)
        print(f"  cleanup_fdm({obj.name}, mode=voxel, voxel={voxel})")
    else:
        print(f"  cleanup_fdm({obj.name}, mode=light)")


# Back-compat aliases
def merge_by_distance_legacy(obj: bpy.types.Object, dist: float = 0.12) -> None:
    merge_by_distance(obj, dist=dist)
