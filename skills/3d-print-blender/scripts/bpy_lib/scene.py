"""Scene + STL export helpers (Blender 4.x headless)."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import bmesh
import bpy
from mathutils import Vector


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.images):
        for b in list(block):
            if b.users == 0:
                block.remove(b)


def set_metric_mm() -> None:
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001  # 1 Blender unit = 1 mm
    scene.unit_settings.length_unit = "MILLIMETERS"


def new_mesh_object(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def set_active(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)


def apply_object_transforms(obj: bpy.types.Object) -> None:
    set_active(obj)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


def mesh_stats(obj: bpy.types.Object) -> dict:
    me = obj.data
    n_tris = sum(len(p.vertices) - 2 for p in me.polygons)
    xs = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    minv = Vector((min(v.x for v in xs), min(v.y for v in xs), min(v.z for v in xs)))
    maxv = Vector((max(v.x for v in xs), max(v.y for v in xs), max(v.z for v in xs)))
    size = maxv - minv
    info = {
        "name": obj.name,
        "tris": n_tris,
        "bbox": (size.x, size.y, size.z),
        "min": (minv.x, minv.y, minv.z),
        "max": (maxv.x, maxv.y, maxv.z),
    }
    print(
        f"  {obj.name}: tris≈{n_tris}  "
        f"bbox={size.x:.2f}x{size.y:.2f}x{size.z:.2f} mm"
    )
    return info


def export_stl(
    obj: bpy.types.Object,
    path: Path | str,
    *,
    apply_transforms: bool = True,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if apply_transforms:
        apply_object_transforms(obj)
    # deselect all, select target
    bpy.ops.object.select_all(action="DESELECT")
    set_active(obj)
    _stl_export(path)
    print(f"Wrote {path} ({path.stat().st_size} bytes)")
    return path


def _stl_export(path: Path) -> None:
    # 4.2+ uses wm.stl_export. Ubuntu's 4.0 package still exposes the name
    # but calling it raises AttributeError — fall back to export_mesh.stl.
    try:
        bpy.ops.wm.stl_export(
            filepath=str(path),
            export_selected_objects=True,
            global_scale=1.0,
            apply_modifiers=True,
            ascii_format=False,
        )
        return
    except Exception:
        bpy.ops.export_mesh.stl(
            filepath=str(path),
            use_selection=True,
            global_scale=1.0,
            use_mesh_modifiers=True,
            ascii=False,
        )


def export_selected_stl(path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _stl_export(path)
    print(f"Wrote {path} ({path.stat().st_size} bytes)")
    return path


def ensure_object_mode() -> None:
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def select_only(objs: Iterable[bpy.types.Object]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    first = None
    for o in objs:
        o.select_set(True)
        if first is None:
            first = o
    if first is not None:
        bpy.context.view_layer.objects.active = first
