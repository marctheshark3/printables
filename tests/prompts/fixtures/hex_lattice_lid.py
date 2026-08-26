#!/usr/bin/env python3
"""Hex honeycomb lid. Prints flat on the bed. Named params match PRINT_SPEC."""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import bmesh
import bpy

_lib = os.environ.get("PBLEND_LIB")
if _lib and _lib not in sys.path:
    sys.path.insert(0, _lib)

from bpy_lib.mesh_ops import merge_by_distance, recalculate_normals_outside  # noqa: E402
from bpy_lib.scene import (  # noqa: E402
    clear_scene,
    export_stl,
    mesh_stats,
    new_mesh_object,
    set_active,
    set_metric_mm,
)

NAME = "organic-lid"
OUTER_X = 80.0
OUTER_Y = 60.0
OUTER_Z = 3.2
HOLE_R = 3.6
WALL = 1.8
RIM = 6.0
CORNER_R = 4.0


def hex_centers(width: float, depth: float) -> list[tuple[float, float]]:
    pitch = 2.0 * HOLE_R + WALL
    dy = pitch * math.sqrt(3.0) / 2.0
    pts = []
    row = 0
    y = RIM + HOLE_R
    while y <= depth - (RIM + HOLE_R):
        x = RIM + HOLE_R + (pitch / 2.0 if row % 2 else 0.0)
        while x <= width - (RIM + HOLE_R):
            pts.append((x, y))
            x += pitch
        y += dy
        row += 1
    return pts


def plate_with_hex_holes() -> bpy.types.Object:
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(OUTER_X, OUTER_Y, OUTER_Z), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(OUTER_X / 2.0, OUTER_Y / 2.0, OUTER_Z / 2.0), verts=bm.verts)
    plate = new_mesh_object(NAME, bm)
    set_active(plate)
    bevel = plate.modifiers.new("Bevel", "BEVEL")
    bevel.width = min(CORNER_R, OUTER_Z / 3)
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    bpy.ops.object.modifier_apply(modifier=bevel.name)

    cutters = []
    for i, (x, y) in enumerate(hex_centers(OUTER_X, OUTER_Y)):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=6,
            radius=HOLE_R,
            depth=OUTER_Z + 4.0,
            location=(x, y, OUTER_Z / 2.0),
        )
        cutter = bpy.context.active_object
        cutter.name = f"hex_{i}"
        cutter.rotation_euler[2] = math.radians(30)
        cutters.append(cutter)

    if cutters:
        set_active(cutters[0])
        for obj in cutters:
            obj.select_set(True)
        if len(cutters) > 1:
            bpy.ops.object.join()
        hive = bpy.context.active_object
        set_active(plate)
        plate.select_set(True)
        hive.select_set(False)
        mod = plate.modifiers.new("honeycomb", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        try:
            mod.solver = "EXACT"
        except TypeError:
            mod.solver = "FAST"
        mod.object = hive
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(hive, do_unlink=True)

    merge_by_distance(plate, 0.04)
    recalculate_normals_outside(plate)
    return plate


def main() -> None:
    root = Path(os.environ.get("PBLEND_PROJECT", Path(__file__).resolve().parent.parent))
    out_dir = root / "stl"
    out_dir.mkdir(parents=True, exist_ok=True)
    clear_scene()
    set_metric_mm()
    part = plate_with_hex_holes()
    mesh_stats(part)
    export_stl(part, out_dir / f"{NAME}.stl")
    print("DONE")


if __name__ == "__main__":
    main()
