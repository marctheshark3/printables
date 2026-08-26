"""Optional PRINT_SPEC assembly, loads, and sim.scene. Imported by print_spec."""
from __future__ import annotations

import math
from typing import Any

from print_spec import (
    DIMENSION_SOURCES,
    AssemblyBody,
    AssemblyJoint,
    HardwareComponent,
    Load,
    Pose,
    SimScene,
    finite_number,
    nested,
)

JOINT_TYPES = {"fixed", "revolute", "prismatic"}
LOAD_KINDS = {"gravity", "point-force", "moment"}
WORLD_PARENTS = {"", "world"}


def vec3(value: Any) -> tuple[float, float, float] | None:
    if not isinstance(value, list) or len(value) != 3:
        return None
    if not all(finite_number(v) for v in value):
        return None
    return (float(value[0]), float(value[1]), float(value[2]))


def world_parent(name: str | None, frame: str | None) -> bool:
    if name is None:
        return True
    if name in WORLD_PARENTS:
        return True
    return frame is not None and name == frame


def stl_body_names(data: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    geometry = data.get("geometry")
    stl_files = geometry.get("stl_files") if isinstance(geometry, dict) else None
    if isinstance(stl_files, list):
        for item in stl_files:
            if isinstance(item, dict) and isinstance(item.get("body"), str) and item["body"]:
                names.add(item["body"])
    return names


def hardware_ids(data: dict[str, Any]) -> dict[str, str]:
    ids: dict[str, str] = {}
    hardware = data.get("hardware")
    components = hardware.get("components") if isinstance(hardware, dict) else None
    if isinstance(components, list):
        for comp in components:
            if isinstance(comp, dict) and isinstance(comp.get("id"), str) and comp["id"]:
                ids[comp["id"]] = str(comp.get("role") or "")
    return ids


def assembly_body_ids(bodies: list) -> set[str]:
    ids: set[str] = set()
    for item in bodies:
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"]:
            ids.add(item["id"])
    return ids


def dimension_parameters(data: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    dimensions = data.get("dimensions")
    if isinstance(dimensions, list):
        for dim in dimensions:
            if isinstance(dim, dict) and isinstance(dim.get("parameter"), str):
                names.add(dim["parameter"])
    return names


def validate_pose(pose: Any, label: str, errors: list[str]) -> None:
    if not isinstance(pose, dict):
        errors.append(f"{label} must be a mapping")
        return
    if "xyz_mm" not in pose:
        errors.append(f"{label}.xyz_mm is required")
    elif vec3(pose.get("xyz_mm")) is None:
        errors.append(f"{label}.xyz_mm must be [X, Y, Z] millimetres")
    if "rpy_deg" not in pose:
        errors.append(f"{label}.rpy_deg is required")
    elif vec3(pose.get("rpy_deg")) is None:
        errors.append(f"{label}.rpy_deg must be [roll, pitch, yaw] degrees")


def required_load_errors(
    *,
    product_class: str | None,
    has_assembly_bodies: bool,
    revolute_children: list[str],
    load_kinds: list[str],
    moment_targets: set[str],
) -> list[str]:
    """Single policy: robot-module + assembly needs gravity and a moment per revolute child."""
    if product_class != "robot-module" or not has_assembly_bodies:
        return []
    errors: list[str] = []
    if "gravity" not in load_kinds:
        errors.append("robot-module assembly requires a gravity load")
    if not revolute_children:
        return errors
    if "moment" not in load_kinds:
        errors.append("robot-module assembly requires a stall moment load at each hub")
        return errors
    for child in revolute_children:
        if child not in moment_targets:
            errors.append(f"robot-module assembly requires a moment load targeting {child}")
    return errors


def _joint_limits(joint: dict[str, Any], jtype: Any, label: str, errors: list[str]) -> None:
    limits = joint.get("limits")
    if jtype == "revolute":
        keys = ("min_deg", "max_deg")
        if not isinstance(limits, dict):
            errors.append(f"{label}.limits is required for revolute joints")
            return
        for key in keys:
            if key not in limits:
                errors.append(f"{label}.limits.{key} is required")
            elif not finite_number(limits.get(key)):
                errors.append(f"{label}.limits.{key} must be a finite number")
        if (
            finite_number(limits.get("min_deg"))
            and finite_number(limits.get("max_deg"))
            and float(limits["max_deg"]) < float(limits["min_deg"])
        ):
            errors.append(f"{label}.limits.max_deg must be >= min_deg")
        return
    if jtype == "prismatic":
        if not isinstance(limits, dict):
            errors.append(f"{label}.limits is required for prismatic joints")
            return
        for key in ("min_mm", "max_mm"):
            if key not in limits:
                errors.append(f"{label}.limits.{key} is required")
            elif not finite_number(limits.get(key)):
                errors.append(f"{label}.limits.{key} must be a finite number")


def validate_assembly(data: dict[str, Any], errors: list[str]) -> None:
    assembly = data.get("assembly")
    if assembly is None:
        return
    if not isinstance(assembly, dict):
        errors.append("assembly must be a mapping")
        return

    frame = assembly.get("frame")
    if not isinstance(frame, str) or not frame:
        errors.append("assembly.frame must be a non-empty string")
        frame = None
    bodies = assembly.get("bodies")
    if not isinstance(bodies, list) or not bodies:
        errors.append("assembly.bodies must be a non-empty list")
        bodies = []

    stl_names = stl_body_names(data)
    hw_ids = hardware_ids(data)
    seen: set[str] = set()
    printed_refs: set[str] = set()
    body_entries: list[dict[str, Any]] = []
    for index, item in enumerate(bodies):
        label = f"assembly.bodies[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be a mapping")
            continue
        body_entries.append(item)
        if "id" not in item:
            errors.append(f"{label}.id is required")
        ident = item.get("id")
        if not isinstance(ident, str) or not ident:
            errors.append(f"{label}.id must be non-empty")
        elif ident in seen:
            errors.append(f"duplicate assembly body id: {ident}")
        else:
            seen.add(ident)
        if "parent" not in item:
            errors.append(f"{label}.parent is required")
        elif not isinstance(item.get("parent"), str) or not item.get("parent"):
            errors.append(f"{label}.parent must be a non-empty string")
        if "pose" not in item:
            errors.append(f"{label}.pose is required")
        else:
            validate_pose(item.get("pose"), f"{label}.pose", errors)
            pose = item.get("pose")
            if isinstance(pose, dict) and "frame" in pose and frame is not None:
                if pose.get("frame") != frame:
                    errors.append(f"{label}.pose.frame must equal assembly.frame")
        has_body = "body" in item and item.get("body") is not None
        has_hw = "hardware" in item and item.get("hardware") is not None
        if has_body == has_hw:
            errors.append(f"{label} must declare exactly one of body or hardware")
            continue
        if has_body:
            ref = item.get("body")
            if not isinstance(ref, str) or not ref:
                errors.append(f"{label}.body must be non-empty")
            elif ref not in stl_names:
                errors.append(f"{label}.body is not a geometry.stl_files body: {ref}")
            else:
                printed_refs.add(ref)
        else:
            ref = item.get("hardware")
            if not isinstance(ref, str) or not ref:
                errors.append(f"{label}.hardware must be non-empty")
            elif ref not in hw_ids:
                errors.append(f"{label}.hardware is not a hardware.components id: {ref}")

    for index, item in enumerate(body_entries):
        parent = item.get("parent")
        ident = item.get("id")
        if not isinstance(parent, str) or not parent:
            continue
        if world_parent(parent, frame):
            continue
        if parent not in seen:
            errors.append(f"assembly.bodies[{index}].parent is not an assembly body id: {parent}")
        elif parent == ident:
            errors.append(f"assembly.bodies[{index}].parent cannot be self")

    product_class = None
    try:
        product_class = nested(data, "part.product_class")
    except KeyError:
        product_class = None
    if product_class == "robot-module" and bodies:
        for name in sorted(stl_names - printed_refs):
            errors.append(f"robot-module assembly is missing printed body: {name}")

    joints = assembly.get("joints")
    if joints is None:
        return
    if not isinstance(joints, list):
        errors.append("assembly.joints must be a list")
        return
    joint_ids: set[str] = set()
    for index, joint in enumerate(joints):
        label = f"assembly.joints[{index}]"
        if not isinstance(joint, dict):
            errors.append(f"{label} must be a mapping")
            continue
        for key in ("id", "type", "parent", "child", "axis", "clearance_per_side_mm", "source"):
            if key not in joint:
                errors.append(f"{label}.{key} is required")
        ident = joint.get("id")
        if not isinstance(ident, str) or not ident:
            errors.append(f"{label}.id must be non-empty")
        elif ident in joint_ids:
            errors.append(f"duplicate assembly joint id: {ident}")
        else:
            joint_ids.add(ident)
        jtype = joint.get("type")
        if "type" in joint and jtype not in JOINT_TYPES:
            errors.append(f"{label}.type must be one of {sorted(JOINT_TYPES)}")
        parent = joint.get("parent")
        if "parent" in joint and (not isinstance(parent, str) or parent not in seen):
            errors.append(f"{label}.parent must name an assembly body")
        child = joint.get("child")
        if "child" in joint and (not isinstance(child, str) or child not in seen):
            errors.append(f"{label}.child must name an assembly body")
        if isinstance(parent, str) and isinstance(child, str) and parent == child:
            errors.append(f"{label}.parent and child must be different")
        axis = vec3(joint.get("axis")) if "axis" in joint else None
        if "axis" in joint and (axis is None or axis == (0.0, 0.0, 0.0)):
            errors.append(f"{label}.axis must be a non-zero [X, Y, Z] vector")
        clearance = joint.get("clearance_per_side_mm")
        if "clearance_per_side_mm" in joint and (not finite_number(clearance) or float(clearance) < 0):
            errors.append(f"{label}.clearance_per_side_mm must be a finite non-negative number")
        source = joint.get("source")
        if "source" in joint and source not in DIMENSION_SOURCES:
            errors.append(f"{label}.source must be one of {sorted(DIMENSION_SOURCES)}")
        elif source == "assumed":
            errors.append(f"{label}.source cannot be assumed")
        _joint_limits(joint, jtype, label, errors)


def validate_loads(data: dict[str, Any], errors: list[str]) -> None:
    loads = data.get("loads")
    parsed: list[dict[str, Any]] = []
    if loads is None:
        errors.extend(_policy_from_mapping(data, parsed))
        return
    if not isinstance(loads, list):
        errors.append("loads must be a list")
        errors.extend(_policy_from_mapping(data, parsed))
        return
    ids: set[str] = set()
    body_ids: set[str] = set()
    assembly = data.get("assembly")
    if isinstance(assembly, dict) and isinstance(assembly.get("bodies"), list):
        body_ids = assembly_body_ids(assembly["bodies"])
    frame = assembly.get("frame") if isinstance(assembly, dict) else None
    hw_ids = set(hardware_ids(data))
    dim_params = dimension_parameters(data)
    for index, load in enumerate(loads):
        label = f"loads[{index}]"
        if not isinstance(load, dict):
            errors.append(f"{label} must be a mapping")
            continue
        parsed.append(load)
        for key in ("id", "kind", "target", "magnitude", "units", "safety_factor", "source"):
            if key not in load:
                errors.append(f"{label}.{key} is required")
        ident = load.get("id")
        if not isinstance(ident, str) or not ident:
            errors.append(f"{label}.id must be non-empty")
        elif ident in ids:
            errors.append(f"duplicate load id: {ident}")
        else:
            ids.add(ident)
        kind = load.get("kind")
        if "kind" in load and kind not in LOAD_KINDS:
            errors.append(f"{label}.kind must be one of {sorted(LOAD_KINDS)}")
        target = load.get("target")
        if "target" in load:
            if not isinstance(target, str) or not target:
                errors.append(f"{label}.target must be non-empty")
            elif not (target in body_ids or target in hw_ids or world_parent(target, frame)):
                errors.append(
                    f"{label}.target must be an assembly body id, hardware id, or assembled frame"
                )
        mag = load.get("magnitude")
        if "magnitude" in load:
            if finite_number(mag):
                pass
            elif vec3(mag) is None:
                errors.append(f"{label}.magnitude must be a finite number or [X, Y, Z]")
        units = load.get("units")
        if "units" in load and (not isinstance(units, str) or not units):
            errors.append(f"{label}.units must be a non-empty string")
        sf = load.get("safety_factor")
        if "safety_factor" in load and (not finite_number(sf) or float(sf) < 1):
            errors.append(f"{label}.safety_factor must be a finite number >= 1")
        source = load.get("source")
        if "source" in load and source not in DIMENSION_SOURCES:
            errors.append(f"{label}.source must be one of {sorted(DIMENSION_SOURCES)}")
        elif source == "assumed":
            errors.append(f"{label}.source cannot be assumed")
        if kind == "moment":
            section = load.get("section")
            if not isinstance(section, dict):
                errors.append(f"{label}.section is required for moment loads")
            else:
                for key in ("outer_parameter", "inner_parameter"):
                    value = section.get(key)
                    if not isinstance(value, str) or not value:
                        errors.append(f"{label}.section.{key} is required")
                    elif value not in dim_params:
                        errors.append(
                            f"{label}.section.{key} must name a dimensions[].parameter"
                        )
    errors.extend(_policy_from_mapping(data, parsed))


def _policy_from_mapping(data: dict[str, Any], loads: list[dict[str, Any]]) -> list[str]:
    try:
        product_class = nested(data, "part.product_class")
    except KeyError:
        product_class = None
    assembly = data.get("assembly")
    bodies = assembly.get("bodies") if isinstance(assembly, dict) else None
    revolute_children: list[str] = []
    joints = assembly.get("joints") if isinstance(assembly, dict) else None
    if isinstance(joints, list):
        for joint in joints:
            if isinstance(joint, dict) and joint.get("type") == "revolute":
                child = joint.get("child")
                if isinstance(child, str) and child:
                    revolute_children.append(child)
    return required_load_errors(
        product_class=product_class if isinstance(product_class, str) else None,
        has_assembly_bodies=isinstance(bodies, list) and bool(bodies),
        revolute_children=revolute_children,
        load_kinds=[str(load.get("kind")) for load in loads if isinstance(load, dict)],
        moment_targets={
            str(load.get("target"))
            for load in loads
            if isinstance(load, dict) and load.get("kind") == "moment" and load.get("target")
        },
    )


def validate_sim(data: dict[str, Any], errors: list[str]) -> None:
    sim = data.get("sim")
    if sim is None:
        return
    if not isinstance(sim, dict):
        errors.append("sim must be a mapping")
        return
    scene = sim.get("scene")
    if scene is None:
        errors.append("sim.scene is required when sim is present")
        return
    if not isinstance(scene, dict):
        errors.append("sim.scene must be a mapping")
        return
    ident = scene.get("id")
    if not isinstance(ident, str) or not ident:
        errors.append("sim.scene.id must be non-empty")
    elif not ident.startswith("table-flat"):
        errors.append("sim.scene.id must start with table-flat")
    gravity = scene.get("gravity_mm_s2")
    if gravity is None:
        errors.append("sim.scene.gravity_mm_s2 is required")
    elif vec3(gravity) is None:
        errors.append("sim.scene.gravity_mm_s2 must be [X, Y, Z] millimetres per second squared")
    floor = scene.get("floor")
    if not isinstance(floor, dict):
        errors.append("sim.scene.floor must be a mapping")
    elif "z_mm" not in floor:
        errors.append("sim.scene.floor.z_mm is required")
    elif not finite_number(floor.get("z_mm")):
        errors.append("sim.scene.floor.z_mm must be a finite number")
    friction = scene.get("friction")
    if not isinstance(friction, dict):
        errors.append("sim.scene.friction must be a mapping")
        return
    if "source" not in friction:
        errors.append("sim.scene.friction.source is required")
    elif friction.get("source") not in DIMENSION_SOURCES:
        errors.append(f"sim.scene.friction.source must be one of {sorted(DIMENSION_SOURCES)}")
    elif friction.get("source") == "assumed":
        errors.append("sim.scene.friction.source cannot be assumed")
    mu = friction.get("mu")
    if mu is None:
        errors.append("sim.scene.friction.mu is required")
    elif not finite_number(mu) or float(mu) < 0:
        errors.append("sim.scene.friction.mu must be a finite non-negative number")


def parse_optional_blocks(data: dict[str, Any]) -> tuple[
    tuple[HardwareComponent, ...],
    str | None,
    tuple[AssemblyBody, ...],
    tuple[AssemblyJoint, ...],
    tuple[Load, ...],
    SimScene | None,
]:
    hardware_comps: list[HardwareComponent] = []
    hardware = data.get("hardware")
    components = hardware.get("components") if isinstance(hardware, dict) else None
    if isinstance(components, list):
        for comp in components:
            envelope = comp["envelope_mm"]
            hardware_comps.append(
                HardwareComponent(
                    id=comp["id"],
                    role=str(comp.get("role") or ""),
                    envelope_mm=(float(envelope[0]), float(envelope[1]), float(envelope[2])),
                )
            )
    assembly = data.get("assembly") if isinstance(data.get("assembly"), dict) else None
    assembly_frame = assembly.get("frame") if assembly else None
    assembly_bodies: list[AssemblyBody] = []
    joints: list[AssemblyJoint] = []
    if assembly:
        for item in assembly.get("bodies") or []:
            pose = item["pose"]
            assembly_bodies.append(
                AssemblyBody(
                    id=item["id"],
                    printed_body=item.get("body") if isinstance(item.get("body"), str) else None,
                    hardware_id=item.get("hardware") if isinstance(item.get("hardware"), str) else None,
                    parent=item["parent"],
                    pose=Pose(
                        xyz_mm=(float(pose["xyz_mm"][0]), float(pose["xyz_mm"][1]), float(pose["xyz_mm"][2])),
                        rpy_deg=(float(pose["rpy_deg"][0]), float(pose["rpy_deg"][1]), float(pose["rpy_deg"][2])),
                    ),
                )
            )
        for joint in assembly.get("joints") or []:
            limits = joint.get("limits")
            limit_pair = None
            if isinstance(limits, dict):
                if joint["type"] == "revolute":
                    limit_pair = (float(limits["min_deg"]), float(limits["max_deg"]))
                elif joint["type"] == "prismatic":
                    limit_pair = (float(limits["min_mm"]), float(limits["max_mm"]))
            ax, ay, az = (float(v) for v in joint["axis"])
            joints.append(
                AssemblyJoint(
                    id=joint["id"],
                    type=joint["type"],
                    parent=joint["parent"],
                    child=joint["child"],
                    axis=(ax, ay, az),
                    limits=limit_pair,
                    clearance_per_side_mm=float(joint["clearance_per_side_mm"]),
                    source=joint["source"],
                )
            )
    loads: list[Load] = []
    for load in data.get("loads") or []:
        mag = load["magnitude"]
        if isinstance(mag, list):
            magnitude = math.sqrt(sum(float(v) ** 2 for v in mag))
            magnitude_xyz = (float(mag[0]), float(mag[1]), float(mag[2]))
        else:
            magnitude = float(mag)
            magnitude_xyz = None
        section = load.get("section") if isinstance(load.get("section"), dict) else {}
        loads.append(
            Load(
                id=load["id"],
                kind=load["kind"],
                target=load["target"],
                magnitude=magnitude,
                magnitude_xyz=magnitude_xyz,
                units=load["units"],
                safety_factor=float(load["safety_factor"]),
                source=load["source"],
                section_outer=section.get("outer_parameter") if load["kind"] == "moment" else None,
                section_inner=section.get("inner_parameter") if load["kind"] == "moment" else None,
            )
        )
    sim_scene = None
    sim = data.get("sim")
    if isinstance(sim, dict) and isinstance(sim.get("scene"), dict):
        scene = sim["scene"]
        gx, gy, gz = scene["gravity_mm_s2"]
        sim_scene = SimScene(
            id=scene["id"],
            gravity_mm_s2=(float(gx), float(gy), float(gz)),
            floor_z_mm=float(scene["floor"]["z_mm"]),
            friction_mu=float(scene["friction"]["mu"]),
            friction_source=scene["friction"]["source"],
        )
    frame = assembly_frame if isinstance(assembly_frame, str) else None
    return tuple(hardware_comps), frame, tuple(assembly_bodies), tuple(joints), tuple(loads), sim_scene
