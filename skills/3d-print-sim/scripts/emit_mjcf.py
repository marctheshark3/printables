#!/usr/bin/env python3
"""One-way MJCF/URDF emit from PRINT_SPEC + STL paths. Never parse the emit back."""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BRIEF = SCRIPTS.parent.parent / "3d-print-design-brief" / "scripts"
VALIDATE = SCRIPTS.parent.parent / "3d-print-validate" / "scripts"
for path in (str(BRIEF), str(VALIDATE)):
    if path not in sys.path:
        sys.path.insert(0, path)

from print_spec import PrintSpec, load_spec  # noqa: E402

SCHEMA = "printables-mjcf-v1"


def _fmt(value: float) -> str:
    return f"{float(value):.3f}"


def _fmt3(vec) -> str:
    return " ".join(_fmt(v) for v in vec)


def emit_mjcf(spec: PrintSpec, stl_dir: str = "stl") -> str:
    """Pinned MJCF v1: compiler degree/local, table-flat plane, bodies in spec order."""
    gravity = spec.sim_scene.gravity_mm_s2 if spec.sim_scene else (0.0, 0.0, -9810.0)
    floor_z = spec.sim_scene.floor_z_mm if spec.sim_scene else 0.0
    lines = [
        f'<mujoco model="{spec.part_name}">',
        f'  <!-- schema {SCHEMA} ; emitted from PRINT_SPEC; not a contract -->',
        '  <compiler angle="degree" coordinate="local" meshdir="{}"/>'.format(stl_dir),
        f'  <option gravity="{_fmt3(gravity)}"/>',
        "  <asset>",
    ]
    seen_mesh: set[str] = set()
    stl_by_body = {item.body: Path(item.path).name for item in spec.stl_files}
    for body in spec.assembly_bodies:
        if body.printed_body and body.printed_body not in seen_mesh:
            seen_mesh.add(body.printed_body)
            filename = stl_by_body[body.printed_body]
            lines.append(f'    <mesh name="{body.printed_body}" file="{filename}"/>')
    lines.append("  </asset>")
    lines.append("  <worldbody>")
    lines.append(
        f'    <geom name="floor" type="plane" size="200.000 200.000 0.100" pos="0.000 0.000 {_fmt(floor_z)}"/>'
    )
    joints_by_child = {joint.child: joint for joint in spec.joints}
    hw_by_id = {item.id: item for item in spec.hardware}
    for body in spec.assembly_bodies:
        lines.append(
            f'    <body name="{body.id}" pos="{_fmt3(body.pose.xyz_mm)}" euler="{_fmt3(body.pose.rpy_deg)}">'
        )
        joint = joints_by_child.get(body.id)
        if joint is not None and joint.type == "revolute" and joint.limits is not None:
            lines.append(
                f'      <joint name="{joint.id}" type="hinge" axis="{_fmt3(joint.axis)}" '
                f'range="{_fmt(joint.limits[0])} {_fmt(joint.limits[1])}"/>'
            )
        elif joint is not None and joint.type == "prismatic" and joint.limits is not None:
            lines.append(
                f'      <joint name="{joint.id}" type="slide" axis="{_fmt3(joint.axis)}" '
                f'range="{_fmt(joint.limits[0])} {_fmt(joint.limits[1])}"/>'
            )
        if body.printed_body:
            lines.append(f'      <geom type="mesh" mesh="{body.printed_body}"/>')
        elif body.hardware_id:
            envelope = hw_by_id[body.hardware_id].envelope_mm
            half = (envelope[0] / 2.0, envelope[1] / 2.0, envelope[2] / 2.0)
            pos = (half[0], half[1], half[2])
            lines.append(
                f'      <geom type="box" size="{_fmt3(half)}" pos="{_fmt3(pos)}"/>'
            )
        lines.append("    </body>")
    lines.append("  </worldbody>")
    lines.append("</mujoco>")
    lines.append("")
    return "\n".join(lines)


def emit_urdf(spec: PrintSpec) -> str:
    lines = [
        '<?xml version="1.0"?>',
        f'<robot name="{spec.part_name}">',
        f"  <!-- schema {SCHEMA} ; emitted from PRINT_SPEC; not a contract -->",
    ]
    stl_by_body = {item.body: item.path for item in spec.stl_files}
    hw_by_id = {item.id: item for item in spec.hardware}
    for body in spec.assembly_bodies:
        lines.append(f'  <link name="{body.id}">')
        lines.append("    <visual>")
        if body.printed_body:
            lines.append("      <geometry>")
            lines.append(
                f'        <mesh filename="{stl_by_body[body.printed_body]}" scale="0.001 0.001 0.001"/>'
            )
            lines.append("      </geometry>")
        elif body.hardware_id:
            envelope = hw_by_id[body.hardware_id].envelope_mm
            lines.append("      <geometry>")
            lines.append(
                f'        <box size="{envelope[0]*0.001:.6f} {envelope[1]*0.001:.6f} {envelope[2]*0.001:.6f}"/>'
            )
            lines.append("      </geometry>")
        lines.append("    </visual>")
        lines.append("  </link>")
    parent_of = {body.id: body.parent for body in spec.assembly_bodies}
    pose_of = {body.id: body.pose for body in spec.assembly_bodies}
    for joint in spec.joints:
        jtype = {"fixed": "fixed", "revolute": "revolute", "prismatic": "prismatic"}[joint.type]
        lines.append(f'  <joint name="{joint.id}" type="{jtype}">')
        lines.append(f'    <parent link="{joint.parent}"/>')
        lines.append(f'    <child link="{joint.child}"/>')
        child_pose = pose_of[joint.child]
        rpy = tuple(math.radians(a) for a in child_pose.rpy_deg)
        xyz = tuple(v * 0.001 for v in child_pose.xyz_mm)
        lines.append(f'    <origin xyz="{_fmt3(xyz)}" rpy="{_fmt3(rpy)}"/>')
        lines.append(f'    <axis xyz="{_fmt3(joint.axis)}"/>')
        if joint.limits is not None and joint.type == "revolute":
            lo, hi = (math.radians(joint.limits[0]), math.radians(joint.limits[1]))
            lines.append(f'    <limit lower="{_fmt(lo)}" upper="{_fmt(hi)}" effort="0" velocity="0"/>')
        lines.append("  </joint>")
        parent_of.pop(joint.child, None)
    for child, parent in parent_of.items():
        if parent in {"", "world"} or (spec.assembly_frame and parent == spec.assembly_frame):
            continue
        if parent not in pose_of or child not in pose_of:
            continue
        child_pose = pose_of[child]
        rpy = tuple(math.radians(a) for a in child_pose.rpy_deg)
        xyz = tuple(v * 0.001 for v in child_pose.xyz_mm)
        lines.append(f'  <joint name="fixed_{child}" type="fixed">')
        lines.append(f'    <parent link="{parent}"/>')
        lines.append(f'    <child link="{child}"/>')
        lines.append(f'    <origin xyz="{_fmt3(xyz)}" rpy="{_fmt3(rpy)}"/>')
        lines.append("  </joint>")
    lines.append("</robot>")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit MJCF/URDF from PRINT_SPEC (one-way)")
    parser.add_argument("project", type=Path)
    parser.add_argument("--spec", default="docs/PRINT_SPEC.yaml")
    parser.add_argument("--format", choices=("mjcf", "urdf"), default="mjcf")
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    spec, errors = load_spec(project / args.spec, project=project, check_files=False)
    if spec is None or errors:
        for error in errors:
            print(f"HARD: {error}", file=sys.stderr)
        return 1
    text = emit_mjcf(spec) if args.format == "mjcf" else emit_urdf(spec)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
