"""Headless stills. Prefer WORKBENCH (more reliable without GPU than EEVEE)."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

import bpy
from mathutils import Vector

from .scene import select_only, set_active


def _frame_camera(cam: bpy.types.Object, targets: Sequence[bpy.types.Object], margin: float = 1.25) -> None:
    # rough orbit framing from combined bbox
    pts = []
    for obj in targets:
        pts.extend(obj.matrix_world @ Vector(c) for c in obj.bound_box)
    if not pts:
        return
    minv = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    maxv = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (minv + maxv) / 2
    size = (maxv - minv).length or 50.0
    dist = size * margin
    cam.location = center + Vector((dist * 0.7, -dist * 0.85, dist * 0.55))
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render_stills(
    objects: Iterable[bpy.types.Object],
    out_dir: Path | str,
    *,
    prefix: str = "part",
    res: Tuple[int, int] = (960, 720),
    views: Optional[Sequence[str]] = None,
) -> list[Path]:
    """Write simple orthographic-ish stills. Returns paths written."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    objs = list(objects)
    if not objs:
        return []
    views = list(views or ("iso", "top", "front"))

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False

    # camera
    if "PBlendCam" in bpy.data.objects:
        cam_obj = bpy.data.objects["PBlendCam"]
    else:
        cam_data = bpy.data.cameras.new("PBlendCam")
        cam_obj = bpy.data.objects.new("PBlendCam", cam_data)
        bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    cam_obj.data.type = "PERSP"
    cam_obj.data.lens = 50

    # hide non-targets
    targets = set(objs)
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = o not in targets

    select_only(objs)
    written: list[Path] = []

    # combined center
    pts = []
    for obj in objs:
        pts.extend(obj.matrix_world @ Vector(c) for c in obj.bound_box)
    minv = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    maxv = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (minv + maxv) / 2
    extent = max((maxv - minv).x, (maxv - minv).y, (maxv - minv).z, 10.0)
    d = extent * 2.2

    placements = {
        "iso": center + Vector((d * 0.7, -d * 0.85, d * 0.55)),
        "top": center + Vector((0.001, 0.001, d * 1.2)),
        "front": center + Vector((0.001, -d * 1.2, d * 0.15)),
        "side": center + Vector((d * 1.2, 0.001, d * 0.15)),
    }

    for view in views:
        loc = placements.get(view)
        if loc is None:
            continue
        cam_obj.location = loc
        direction = center - cam_obj.location
        cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        path = out_dir / f"{prefix}-{view}.png"
        scene.render.filepath = str(path)
        try:
            bpy.ops.render.render(write_still=True)
            if path.is_file() and path.stat().st_size > 0:
                print(f"Preview {path} ({path.stat().st_size} bytes)")
                written.append(path)
            else:
                print(f"WARN empty preview {path}")
        except Exception as exc:  # noqa: BLE001 — headless GL can fail
            print(f"WARN render failed ({view}): {exc}")

    return written
