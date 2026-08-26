"""Blender -P helper: STL stills — one mesh at a time by default (FDM craft).

Usage:
  blender -b -P bpy_preview_runner.py -- --project DIR [--prefix name] [--together]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from bpy_lib.preview import render_stills  # noqa: E402
from bpy_lib.scene import clear_scene, set_metric_mm  # noqa: E402


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True)
    p.add_argument("--prefix", default="part")
    p.add_argument("--objects", default=None)
    p.add_argument(
        "--together",
        action="store_true",
        help="Render all meshes in one frame (default: separate per STL)",
    )
    return p.parse_args(argv)


def import_stls(stl_dir: Path) -> list:
    objs = []
    for stl in sorted(stl_dir.glob("*.stl")):
        if "assembly" in stl.name.lower():
            continue
        before = set(bpy.data.objects)
        try:
            bpy.ops.wm.stl_import(filepath=str(stl))
        except Exception:
            try:
                bpy.ops.import_mesh.stl(filepath=str(stl))
            except Exception as exc:
                print(f"WARN import failed {stl}: {exc}")
                continue
        after = [o for o in bpy.data.objects if o not in before]
        for o in after:
            o.name = stl.stem
            objs.append(o)
    return objs


def main():
    args = parse_args()
    project = Path(args.project)
    out_dir = project / "renders"
    out_dir.mkdir(parents=True, exist_ok=True)

    clear_scene()
    set_metric_mm()
    objs = import_stls(project / "stl")
    if args.objects:
        want = {n.strip() for n in args.objects.split(",") if n.strip()}
        objs = [o for o in objs if o.name in want]
    if not objs:
        print("ERROR: no mesh objects to preview")
        sys.exit(1)

    written = []
    if args.together:
        written = render_stills(objs, out_dir, prefix=args.prefix)
    else:
        for o in objs:
            o.hide_render = True
        for o in objs:
            for x in objs:
                x.hide_render = x is not o
            pref = o.name.replace(" ", "-")
            written.extend(render_stills([o], out_dir, prefix=pref))

    if not written:
        print("WARN: no previews written")
        sys.exit(0)
    print(f"Wrote {len(written)} previews")
    sys.exit(0)


if __name__ == "__main__":
    main()
