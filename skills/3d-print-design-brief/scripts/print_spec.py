#!/usr/bin/env python3
"""Machine-readable CAD/CAM contract: docs/PRINT_SPEC.yaml."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise SystemExit("HARD: PyYAML is required: python3 -m pip install PyYAML") from exc


BACKENDS = {"openscad", "blender", "hybrid"}
PRODUCT_CLASSES = {
    "bracket", "mount", "stand", "tray", "enclosure", "equipment-open-frame",
    "wet-fixture", "pip-hinge", "silhouette", "robot-module", "other",
}
FIT_EVIDENCE = {"measured", "from-user", "datasheet", "fit-tested", "assumed", "none"}
REQUIRED_FIT_EVIDENCE = {"measured", "from-user", "datasheet", "fit-tested"}
DIMENSION_SOURCES = {"measured", "from-user", "datasheet", "fit-tested", "assumed"}
SUPPORT_POLICIES = {"none", "build-plate-only", "required"}
SERVICE_ENVIRONMENTS = {"dry", "wet"}
DRAINAGE = {
    "none",
    "not-applicable",
    "unspecified",
    "open-continuous",
    "through-drain",
    "drainable",
    "slots",
}
POSITIVE_DRAINAGE = {
    "open-continuous",
    "through-drain",
    "drainable",
    "slots",
}
COUPON_SUFFIXES = {".stl", ".scad", ".py", ".yaml", ".yml", ".md"}
CRITICAL_HARDWARE_ROLES = {"mcu", "servo", "motor", "drive"}
JOINT_TYPES = {"fixed", "revolute", "prismatic"}
LOAD_KINDS = {"gravity", "point-force", "moment"}
WORLD_PARENTS = {"", "world"}
VOLT_ALIASES = {
    "3V3": 3.3, "3.3V": 3.3, "3.3": 3.3, "+3V3": 3.3,
    "5V": 5.0, "5.0V": 5.0, "5": 5.0, "5.0": 5.0, "+5V": 5.0,
    "GND": 0.0, "0V": 0.0, "0": 0.0, "0.0": 0.0,
}

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_LINE_COMMENT = re.compile(r"//.*?$", re.M)
_HASH_COMMENT = re.compile(r"#.*?$", re.M)


@dataclass(frozen=True)
class StlBody:
    path: str
    body: str
    expected_shells: int


@dataclass(frozen=True)
class Dimension:
    name: str
    parameter: str
    value_mm: float
    tolerance_mm: float
    source: str


@dataclass(frozen=True)
class HardwareComponent:
    id: str
    role: str
    envelope_mm: tuple[float, float, float]


@dataclass(frozen=True)
class Pose:
    xyz_mm: tuple[float, float, float]
    rpy_deg: tuple[float, float, float]


@dataclass(frozen=True)
class AssemblyBody:
    id: str
    printed_body: str | None
    hardware_id: str | None
    parent: str
    pose: Pose


@dataclass(frozen=True)
class AssemblyJoint:
    id: str
    type: str
    parent: str
    child: str
    axis: tuple[float, float, float]
    limits: tuple[float, float] | None
    clearance_per_side_mm: float
    source: str


@dataclass(frozen=True)
class Load:
    id: str
    kind: str
    target: str
    magnitude: float
    units: str
    safety_factor: float
    source: str


@dataclass(frozen=True)
class SimScene:
    id: str
    gravity_mm_s2: tuple[float, float, float]
    floor_z_mm: float
    friction_mu: float
    friction_source: str


@dataclass(frozen=True)
class PrintSpec:
    """Validated manufacturing contract. One object, many exported bodies."""

    schema_version: int
    part_name: str
    revision: str
    product_class: str
    purpose: str
    process: str
    printer: str
    build_volume_mm: tuple[float, float, float]
    material: str
    nozzle_mm: float
    layer_height_mm: float
    backend: str
    source_files: tuple[str, ...]
    min_wall_mm: float
    min_feature_mm: float
    stl_files: tuple[StlBody, ...]
    fit_required: bool
    clearance_per_side_mm: float
    fit_evidence: str
    fit_coupon: str | None
    dimensions: tuple[Dimension, ...]
    orientation: str
    bed_face: str
    up_axis: str
    supports: str
    max_overhang_deg: float
    service_environment: str
    drainage: str
    extra_parameters: tuple[str, ...]
    hardware: tuple[HardwareComponent, ...]
    assembly_frame: str | None
    assembly_bodies: tuple[AssemblyBody, ...]
    joints: tuple[AssemblyJoint, ...]
    loads: tuple[Load, ...]
    sim_scene: SimScene | None


def nested(data: dict[str, Any], path: str) -> Any:
    value: Any = data
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            raise KeyError(path)
        value = value[key]
    return value


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def safe_relative_path(value: str) -> bool:
    path = Path(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts


def coupon_is_path(coupon: str) -> bool:
    return "/" in coupon or Path(coupon).suffix.lower() in COUPON_SUFFIXES


def parse_volts(value: Any) -> float | None:
    if finite_number(value):
        return float(value)
    if not isinstance(value, str):
        return None
    text = value.strip().upper().replace(" ", "")
    if text in VOLT_ALIASES:
        return VOLT_ALIASES[text]
    try:
        return float(text.replace("V", ""))
    except ValueError:
        return None


def logic_rail(volts: float) -> str | None:
    if abs(volts - 3.3) <= 0.2:
        return "3v3"
    if abs(volts - 5.0) <= 0.2:
        return "5v"
    return None


def validate_named_millimetre(
    dim: Any, label: str, errors: list[str], names: set[str] | None = None
) -> None:
    if not isinstance(dim, dict):
        errors.append(f"{label} must be a mapping")
        return
    for key in ("name", "parameter", "value_mm", "tolerance_mm", "source"):
        if key not in dim:
            errors.append(f"{label}.{key} is required")
    name = dim.get("name")
    if not isinstance(name, str) or not name:
        errors.append(f"{label}.name must be non-empty")
    elif names is not None:
        if name in names:
            errors.append(f"duplicate dimension name: {name}")
        else:
            names.add(name)
    parameter = dim.get("parameter")
    if not isinstance(parameter, str) or not parameter.isidentifier():
        errors.append(f"{label}.parameter must be a valid CAD identifier")
    for key in ("value_mm", "tolerance_mm"):
        if key in dim and (not finite_number(dim[key]) or float(dim[key]) < 0):
            errors.append(f"{label}.{key} must be a finite non-negative number")
    if "source" in dim and dim.get("source") not in DIMENSION_SOURCES:
        errors.append(f"{label}.source must be one of {sorted(DIMENSION_SOURCES)}")


def extra_cad_parameters(data: dict[str, Any]) -> tuple[str, ...]:
    params: list[str] = []
    hardware = data.get("hardware")
    if isinstance(hardware, dict):
        components = hardware.get("components")
        if isinstance(components, list):
            for comp in components:
                if not isinstance(comp, dict):
                    continue
                interfaces = comp.get("interfaces")
                if isinstance(interfaces, list):
                    for iface in interfaces:
                        if isinstance(iface, dict) and isinstance(iface.get("parameter"), str):
                            params.append(iface["parameter"])
    wiring = data.get("wiring")
    if isinstance(wiring, dict):
        for key in ("connector_keepouts", "cable_path_keepouts"):
            items = wiring.get(key)
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and isinstance(item.get("parameter"), str):
                        params.append(item["parameter"])
    return tuple(params)


def _validate_keepout_list(items: Any, label: str, errors: list[str]) -> None:
    if not isinstance(items, list):
        errors.append(f"{label} must be a list")
        return
    names: set[str] = set()
    for index, item in enumerate(items):
        entry = f"{label}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{entry} must be a mapping")
            continue
        for key in ("name", "parameter", "width_mm", "height_mm", "source"):
            if key not in item:
                errors.append(f"{entry}.{key} is required")
        name = item.get("name")
        if not isinstance(name, str) or not name:
            errors.append(f"{entry}.name must be non-empty")
        elif name in names:
            errors.append(f"duplicate keepout name: {name}")
        else:
            names.add(name)
        parameter = item.get("parameter")
        if not isinstance(parameter, str) or not parameter.isidentifier():
            errors.append(f"{entry}.parameter must be a valid CAD identifier")
        for key in ("width_mm", "height_mm", "depth_mm", "length_mm"):
            if key in item and (not finite_number(item[key]) or float(item[key]) < 0):
                errors.append(f"{entry}.{key} must be a finite non-negative number")
        if "source" in item and item.get("source") not in DIMENSION_SOURCES:
            errors.append(f"{entry}.source must be one of {sorted(DIMENSION_SOURCES)}")


def validate_hardware(data: dict[str, Any], errors: list[str]) -> None:
    product_class = nested(data, "part.product_class")
    hardware = data.get("hardware")
    if product_class == "robot-module":
        components = hardware.get("components") if isinstance(hardware, dict) else None
        if not isinstance(hardware, dict) or not isinstance(components, list) or not components:
            errors.append("robot-module requires non-empty hardware.components")
            if not isinstance(hardware, dict):
                return
    elif hardware is None:
        return
    elif not isinstance(hardware, dict):
        errors.append("hardware must be a mapping")
        return

    components = hardware.get("components")
    if components is None:
        return
    if not isinstance(components, list):
        errors.append("hardware.components must be a list")
        return

    ids: set[str] = set()
    for index, comp in enumerate(components):
        label = f"hardware.components[{index}]"
        if not isinstance(comp, dict):
            errors.append(f"{label} must be a mapping")
            continue
        for key in ("id", "mpn_or_generic", "role", "qty", "envelope_mm", "interfaces"):
            if key not in comp:
                errors.append(f"{label}.{key} is required")
        ident = comp.get("id")
        if not isinstance(ident, str) or not ident:
            errors.append(f"{label}.id must be non-empty")
        elif ident in ids:
            errors.append(f"duplicate hardware component id: {ident}")
        else:
            ids.add(ident)
        mpn = comp.get("mpn_or_generic")
        if "mpn_or_generic" in comp and (not isinstance(mpn, str) or not mpn):
            errors.append(f"{label}.mpn_or_generic must be non-empty")
        role = comp.get("role")
        if "role" in comp and (not isinstance(role, str) or not role):
            errors.append(f"{label}.role must be non-empty")
        qty = comp.get("qty")
        if "qty" in comp and (not isinstance(qty, int) or isinstance(qty, bool) or qty < 1):
            errors.append(f"{label}.qty must be an integer >= 1")
        envelope = comp.get("envelope_mm")
        if "envelope_mm" in comp and (
            not isinstance(envelope, list) or len(envelope) != 3
            or not all(finite_number(value) and float(value) > 0 for value in envelope)
        ):
            errors.append(f"{label}.envelope_mm must be [X, Y, Z] positive millimetres")
        interfaces = comp.get("interfaces")
        if "interfaces" not in comp:
            continue
        if not isinstance(interfaces, list):
            errors.append(f"{label}.interfaces must be a list")
            continue
        if role in CRITICAL_HARDWARE_ROLES and not interfaces:
            errors.append(f"{label}.interfaces must be non-empty for critical role {role}")
        names: set[str] = set()
        for iface_index, iface in enumerate(interfaces):
            iface_label = f"{label}.interfaces[{iface_index}]"
            validate_named_millimetre(iface, iface_label, errors, names)
            if (
                role in CRITICAL_HARDWARE_ROLES
                and isinstance(iface, dict)
                and iface.get("source") == "assumed"
            ):
                errors.append(
                    f"{iface_label}.source cannot be assumed for critical role {role}"
                )


def _vec3(value: Any) -> tuple[float, float, float] | None:
    if not isinstance(value, list) or len(value) != 3:
        return None
    if not all(finite_number(v) for v in value):
        return None
    return (float(value[0]), float(value[1]), float(value[2]))


def _world_parent(name: str | None, frame: str | None) -> bool:
    if name is None:
        return True
    if name in WORLD_PARENTS:
        return True
    if frame is not None and name == frame:
        return True
    return False


def validate_pose(pose: Any, label: str, errors: list[str]) -> None:
    if not isinstance(pose, dict):
        errors.append(f"{label} must be a mapping")
        return
    if "xyz_mm" not in pose:
        errors.append(f"{label}.xyz_mm is required")
    elif _vec3(pose.get("xyz_mm")) is None:
        errors.append(f"{label}.xyz_mm must be [X, Y, Z] millimetres")
    if "rpy_deg" not in pose:
        errors.append(f"{label}.rpy_deg is required")
    elif _vec3(pose.get("rpy_deg")) is None:
        errors.append(f"{label}.rpy_deg must be [roll, pitch, yaw] degrees")


def _stl_body_names(data: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    stl_files = data.get("geometry", {}).get("stl_files") if isinstance(data.get("geometry"), dict) else None
    if isinstance(stl_files, list):
        for item in stl_files:
            if isinstance(item, dict) and isinstance(item.get("body"), str) and item["body"]:
                names.add(item["body"])
    return names


def _hardware_ids(data: dict[str, Any]) -> dict[str, str]:
    ids: dict[str, str] = {}
    hardware = data.get("hardware")
    components = hardware.get("components") if isinstance(hardware, dict) else None
    if isinstance(components, list):
        for comp in components:
            if isinstance(comp, dict) and isinstance(comp.get("id"), str) and comp["id"]:
                ids[comp["id"]] = str(comp.get("role") or "")
    return ids


def _assembly_body_ids(bodies: list) -> set[str]:
    ids: set[str] = set()
    for item in bodies:
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"]:
            ids.add(item["id"])
    return ids


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

    stl_names = _stl_body_names(data)
    hw_ids = _hardware_ids(data)
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
        if _world_parent(parent, frame):
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
        missing_printed = stl_names - printed_refs
        for name in sorted(missing_printed):
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
        axis = _vec3(joint.get("axis")) if "axis" in joint else None
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
        limits = joint.get("limits")
        if jtype == "revolute":
            if not isinstance(limits, dict):
                errors.append(f"{label}.limits is required for revolute joints")
            else:
                if "min_deg" not in limits:
                    errors.append(f"{label}.limits.min_deg is required")
                if "max_deg" not in limits:
                    errors.append(f"{label}.limits.max_deg is required")
                if "min_deg" in limits and not finite_number(limits.get("min_deg")):
                    errors.append(f"{label}.limits.min_deg must be a finite number")
                if "max_deg" in limits and not finite_number(limits.get("max_deg")):
                    errors.append(f"{label}.limits.max_deg must be a finite number")
                if (
                    finite_number(limits.get("min_deg"))
                    and finite_number(limits.get("max_deg"))
                    and float(limits["max_deg"]) < float(limits["min_deg"])
                ):
                    errors.append(f"{label}.limits.max_deg must be >= min_deg")
        elif jtype == "prismatic":
            if not isinstance(limits, dict):
                errors.append(f"{label}.limits is required for prismatic joints")
            else:
                if "min_mm" not in limits:
                    errors.append(f"{label}.limits.min_mm is required")
                if "max_mm" not in limits:
                    errors.append(f"{label}.limits.max_mm is required")
                if "min_mm" in limits and (not finite_number(limits.get("min_mm"))):
                    errors.append(f"{label}.limits.min_mm must be a finite number")
                if "max_mm" in limits and (not finite_number(limits.get("max_mm"))):
                    errors.append(f"{label}.limits.max_mm must be a finite number")


def validate_loads(data: dict[str, Any], errors: list[str]) -> None:
    loads = data.get("loads")
    if loads is None:
        _require_robot_module_loads(data, errors, [])
        return
    if not isinstance(loads, list):
        errors.append("loads must be a list")
        _require_robot_module_loads(data, errors, [])
        return
    ids: set[str] = set()
    parsed: list[dict[str, Any]] = []
    body_ids = set()
    assembly = data.get("assembly")
    if isinstance(assembly, dict) and isinstance(assembly.get("bodies"), list):
        body_ids = _assembly_body_ids(assembly["bodies"])
    frame = assembly.get("frame") if isinstance(assembly, dict) else None
    hw_ids = set(_hardware_ids(data))
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
            elif not (
                target in body_ids
                or target in hw_ids
                or _world_parent(target, frame)
            ):
                errors.append(
                    f"{label}.target must be an assembly body id, hardware id, or assembled frame"
                )
        mag = load.get("magnitude")
        if "magnitude" in load:
            if finite_number(mag):
                pass
            elif _vec3(mag) is None:
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
    _require_robot_module_loads(data, errors, parsed)


def _require_robot_module_loads(
    data: dict[str, Any], errors: list[str], loads: list[dict[str, Any]]
) -> None:
    try:
        product_class = nested(data, "part.product_class")
    except KeyError:
        return
    assembly = data.get("assembly")
    bodies = assembly.get("bodies") if isinstance(assembly, dict) else None
    if product_class != "robot-module" or not isinstance(bodies, list) or not bodies:
        return
    kinds = [load.get("kind") for load in loads if isinstance(load, dict)]
    if "gravity" not in kinds:
        errors.append("robot-module assembly requires a gravity load")
    joints = assembly.get("joints") if isinstance(assembly, dict) else None
    revolute_children: list[str] = []
    if isinstance(joints, list):
        for joint in joints:
            if isinstance(joint, dict) and joint.get("type") == "revolute":
                child = joint.get("child")
                if isinstance(child, str) and child:
                    revolute_children.append(child)
    hw_roles = _hardware_ids(data)
    assembly_hw: list[str] = []
    for item in bodies:
        if not isinstance(item, dict):
            continue
        hid = item.get("hardware")
        if isinstance(hid, str) and hw_roles.get(hid) in {"motor", "drive"}:
            assembly_hw.append(hid)
    moment_targets = {
        load.get("target")
        for load in loads
        if isinstance(load, dict) and load.get("kind") == "moment"
    }
    if revolute_children or assembly_hw:
        covered = set()
        for child in revolute_children:
            if child in moment_targets:
                covered.add(child)
        if not any(load.get("kind") == "moment" for load in loads if isinstance(load, dict)):
            errors.append("robot-module assembly requires a stall moment load at each hub")
        else:
            missing = [child for child in revolute_children if child not in moment_targets]
            for child in missing:
                errors.append(f"robot-module assembly requires a moment load targeting {child}")


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
    elif _vec3(gravity) is None:
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
    else:
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


def validate_wiring(data: dict[str, Any], errors: list[str]) -> None:
    wiring = data.get("wiring")
    if wiring is None:
        return
    if not isinstance(wiring, dict):
        errors.append("wiring must be a mapping")
        return

    domains = wiring.get("voltage_domains")
    if not isinstance(domains, list) or not domains:
        errors.append("wiring.voltage_domains must be a non-empty list")
        domains = []
    domain_volts: dict[str, float] = {}
    domain_names: set[str] = set()
    for index, domain in enumerate(domains):
        label = f"wiring.voltage_domains[{index}]"
        if not isinstance(domain, dict):
            errors.append(f"{label} must be a mapping")
            continue
        if "name" not in domain or "volts" not in domain:
            if "name" not in domain:
                errors.append(f"{label}.name is required")
            if "volts" not in domain:
                errors.append(f"{label}.volts is required")
        name = domain.get("name")
        if not isinstance(name, str) or not name:
            errors.append(f"{label}.name must be non-empty")
        elif name in domain_names:
            errors.append(f"duplicate voltage domain: {name}")
        else:
            domain_names.add(name)
        volts = parse_volts(domain.get("volts"))
        if volts is None:
            errors.append(f"{label}.volts must be a finite number or voltage label")
        elif isinstance(name, str) and name:
            domain_volts[name] = volts

    pin_map = wiring.get("pin_map")
    nets = wiring.get("nets")
    has_pins = isinstance(pin_map, list) and bool(pin_map)
    has_nets = isinstance(nets, list) and bool(nets)
    if pin_map is not None and not isinstance(pin_map, list):
        errors.append("wiring.pin_map must be a list")
    if nets is not None and not isinstance(nets, list):
        errors.append("wiring.nets must be a list")
    if not has_pins and not has_nets:
        errors.append("wiring requires nets or pin_map")

    pin_rails: dict[str, set[str]] = {}
    net_rails: dict[str, set[str]] = {}

    if isinstance(nets, list):
        net_names: set[str] = set()
        for index, net in enumerate(nets):
            label = f"wiring.nets[{index}]"
            if not isinstance(net, dict):
                errors.append(f"{label} must be a mapping")
                continue
            if "name" not in net:
                errors.append(f"{label}.name is required")
            if "voltage_domain" not in net:
                errors.append(f"{label}.voltage_domain is required")
            name = net.get("name")
            if not isinstance(name, str) or not name:
                errors.append(f"{label}.name must be non-empty")
            elif name in net_names:
                errors.append(f"duplicate net name: {name}")
            else:
                net_names.add(name)
            domain = net.get("voltage_domain")
            if domain is not None and domain not in domain_volts:
                errors.append(f"{label}.voltage_domain must name a voltage_domains entry")
            volts = domain_volts.get(domain) if isinstance(domain, str) else None
            rail = logic_rail(volts) if volts is not None else None
            if rail and isinstance(name, str) and name:
                net_rails.setdefault(name, set()).add(rail)

    if isinstance(pin_map, list):
        for index, pin in enumerate(pin_map):
            label = f"wiring.pin_map[{index}]"
            if not isinstance(pin, dict):
                errors.append(f"{label} must be a mapping")
                continue
            for key in ("mcu_pin", "function", "voltage"):
                if key not in pin:
                    errors.append(f"{label}.{key} is required")
            mcu_pin = pin.get("mcu_pin")
            if "mcu_pin" in pin and (not isinstance(mcu_pin, str) or not mcu_pin):
                errors.append(f"{label}.mcu_pin must be non-empty")
            function = pin.get("function")
            if "function" in pin and (not isinstance(function, str) or not function):
                errors.append(f"{label}.function must be non-empty")
            volts = parse_volts(pin.get("voltage")) if "voltage" in pin else None
            if "voltage" in pin and volts is None:
                errors.append(f"{label}.voltage must be a finite number or voltage label")
            rail = logic_rail(volts) if volts is not None else None
            if rail and isinstance(mcu_pin, str) and mcu_pin:
                pin_rails.setdefault(mcu_pin, set()).add(rail)
            net = pin.get("net")
            if net is not None and (not isinstance(net, str) or not net):
                errors.append(f"{label}.net must be a non-empty string")
            elif isinstance(net, str) and rail:
                net_rails.setdefault(net, set()).add(rail)

    for pin, rails in pin_rails.items():
        if "3v3" in rails and "5v" in rails:
            errors.append(f"wiring 3V3/5V collision on pin {pin}")
    for net, rails in net_rails.items():
        if "3v3" in rails and "5v" in rails:
            errors.append(f"wiring 3V3/5V collision on net {net}")

    if "connector_keepouts" not in wiring:
        errors.append("wiring.connector_keepouts is required")
    else:
        _validate_keepout_list(wiring.get("connector_keepouts"), "wiring.connector_keepouts", errors)
    if "cable_path_keepouts" not in wiring:
        errors.append("wiring.cable_path_keepouts is required")
    else:
        _validate_keepout_list(
            wiring.get("cable_path_keepouts"), "wiring.cable_path_keepouts", errors
        )


def validate(data: Any, project: Path | None = None, check_files: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be a mapping"]

    required = [
        "schema_version", "part.name", "part.revision", "part.product_class", "part.purpose",
        "manufacturing.process", "manufacturing.printer", "manufacturing.build_volume_mm",
        "manufacturing.material", "manufacturing.nozzle_mm", "manufacturing.layer_height_mm",
        "cad.backend", "cad.parametric", "cad.units", "cad.source_files",
        "geometry.min_wall_mm", "geometry.min_feature_mm",
        "geometry.overlapping_solids_allowed", "geometry.stl_files",
        "fit.required", "fit.clearance_per_side_mm", "fit.evidence",
        "dimensions", "print.orientation", "print.bed_face", "print.up_axis",
        "print.supports", "print.max_overhang_deg",
        "service.environment", "service.drainage",
    ]
    for path in required:
        try:
            nested(data, path)
        except KeyError:
            errors.append(f"missing required key: {path}")
    if errors:
        return errors

    if data["schema_version"] != 1:
        errors.append("schema_version must equal 1")
    if nested(data, "manufacturing.process") != "fdm":
        errors.append("manufacturing.process must be fdm")
    if nested(data, "part.product_class") not in PRODUCT_CLASSES:
        errors.append(f"part.product_class must be one of {sorted(PRODUCT_CLASSES)}")
    build_volume = nested(data, "manufacturing.build_volume_mm")
    if (
        not isinstance(build_volume, list) or len(build_volume) != 3
        or not all(finite_number(value) and float(value) > 0 for value in build_volume)
    ):
        errors.append("manufacturing.build_volume_mm must be [X, Y, Z] positive millimetres")
    if nested(data, "cad.backend") not in BACKENDS:
        errors.append(f"cad.backend must be one of {sorted(BACKENDS)}")
    if nested(data, "cad.parametric") is not True:
        errors.append("cad.parametric must be true")
    if nested(data, "cad.units") != "mm":
        errors.append("cad.units must be mm")
    if nested(data, "geometry.overlapping_solids_allowed") is not False:
        errors.append("geometry.overlapping_solids_allowed must be false")
    if nested(data, "print.up_axis") != "Z":
        errors.append("print.up_axis must be Z")
    if nested(data, "print.supports") not in SUPPORT_POLICIES:
        errors.append(f"print.supports must be one of {sorted(SUPPORT_POLICIES)}")
    if nested(data, "service.environment") not in SERVICE_ENVIRONMENTS:
        errors.append(f"service.environment must be one of {sorted(SERVICE_ENVIRONMENTS)}")
    if nested(data, "service.drainage") not in DRAINAGE:
        errors.append(f"service.drainage must be one of {sorted(DRAINAGE)}")

    for path in (
        "manufacturing.nozzle_mm", "manufacturing.layer_height_mm",
        "geometry.min_wall_mm", "geometry.min_feature_mm",
        "fit.clearance_per_side_mm", "print.max_overhang_deg",
    ):
        value = nested(data, path)
        if not finite_number(value) or float(value) < 0:
            errors.append(f"{path} must be a finite non-negative number")

    nozzle = nested(data, "manufacturing.nozzle_mm")
    if finite_number(nozzle):
        if float(nested(data, "geometry.min_wall_mm")) < float(nozzle) * 2:
            errors.append("geometry.min_wall_mm must be at least 2x nozzle_mm")
        if float(nested(data, "geometry.min_feature_mm")) < float(nozzle) * 2:
            errors.append("geometry.min_feature_mm must be at least 2x nozzle_mm")

    source_files = nested(data, "cad.source_files")
    if not isinstance(source_files, list) or not source_files or not all(
        isinstance(x, str) and safe_relative_path(x) for x in source_files
    ):
        errors.append("cad.source_files must be a non-empty list of project-relative paths without '..'")

    stl_files = nested(data, "geometry.stl_files")
    if not isinstance(stl_files, list) or not stl_files:
        errors.append("geometry.stl_files must be a non-empty list")
    else:
        seen: set[str] = set()
        for index, item in enumerate(stl_files):
            label = f"geometry.stl_files[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be a mapping")
                continue
            for key in ("path", "body", "expected_shells"):
                if key not in item:
                    errors.append(f"{label}.{key} is required")
            path = item.get("path")
            if isinstance(path, str):
                if not safe_relative_path(path):
                    errors.append(f"{label}.path must be project-relative and cannot contain '..'")
                if path in seen:
                    errors.append(f"duplicate STL path: {path}")
                seen.add(path)
            shells = item.get("expected_shells")
            if not isinstance(shells, int) or isinstance(shells, bool) or shells < 1:
                errors.append(f"{label}.expected_shells must be an integer >= 1")

    evidence = nested(data, "fit.evidence")
    if evidence not in FIT_EVIDENCE:
        errors.append(f"fit.evidence must be one of {sorted(FIT_EVIDENCE)}")
    coupon = data.get("fit", {}).get("coupon")
    if nested(data, "fit.required") is True:
        if evidence not in REQUIRED_FIT_EVIDENCE:
            errors.append("required fit needs measured, from-user, datasheet, or fit-tested evidence")
        if evidence != "fit-tested" and not coupon:
            errors.append("required fit needs fit.coupon unless evidence is fit-tested")
    elif nested(data, "fit.required") is not False:
        errors.append("fit.required must be true or false")
    if isinstance(coupon, str) and coupon and coupon_is_path(coupon) and not safe_relative_path(coupon):
        errors.append("fit.coupon must be a project-relative path without '..'")

    dimensions = data.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        errors.append("dimensions must be a non-empty list")
    else:
        names: set[str] = set()
        for index, dim in enumerate(dimensions):
            validate_named_millimetre(dim, f"dimensions[{index}]", errors, names)

    validate_hardware(data, errors)
    validate_wiring(data, errors)
    validate_assembly(data, errors)
    validate_loads(data, errors)
    validate_sim(data, errors)

    if nested(data, "service.environment") == "wet":
        if nested(data, "service.drainage") not in POSITIVE_DRAINAGE:
            errors.append("wet service requires positive drainage")
        if str(nested(data, "manufacturing.material")).upper() == "PLA":
            errors.append("wet service cannot use PLA")

    if check_files and project is not None:
        paths: list[str] = []
        if isinstance(source_files, list):
            paths.extend(x for x in source_files if isinstance(x, str))
        if isinstance(stl_files, list):
            for item in stl_files:
                if isinstance(item, dict):
                    rel = item.get("path")
                    if isinstance(rel, str):
                        paths.append(rel)
        if isinstance(coupon, str) and coupon and safe_relative_path(coupon) and coupon_is_path(coupon):
            paths.append(coupon)
        for rel in paths:
            if not safe_relative_path(rel):
                continue
            if not (project / rel).is_file():
                errors.append(f"declared file does not exist: {rel}")

    return errors


def parse_spec(data: dict[str, Any]) -> PrintSpec:
    """Build a PrintSpec. Call only after validate() returned no errors."""
    bx, by, bz = nested(data, "manufacturing.build_volume_mm")
    coupon = data.get("fit", {}).get("coupon")
    bodies = tuple(
        StlBody(path=item["path"], body=item["body"], expected_shells=item["expected_shells"])
        for item in nested(data, "geometry.stl_files")
    )
    dimensions = tuple(
        Dimension(
            name=dim["name"],
            parameter=dim["parameter"],
            value_mm=float(dim["value_mm"]),
            tolerance_mm=float(dim["tolerance_mm"]),
            source=dim["source"],
        )
        for dim in data["dimensions"]
    )
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
            parent = item["parent"]
            assembly_bodies.append(
                AssemblyBody(
                    id=item["id"],
                    printed_body=item.get("body") if isinstance(item.get("body"), str) else None,
                    hardware_id=item.get("hardware") if isinstance(item.get("hardware"), str) else None,
                    parent=parent,
                    pose=Pose(
                        xyz_mm=tuple(float(v) for v in pose["xyz_mm"]),  # type: ignore[arg-type]
                        rpy_deg=tuple(float(v) for v in pose["rpy_deg"]),  # type: ignore[arg-type]
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
            axis = tuple(float(v) for v in joint["axis"])
            joints.append(
                AssemblyJoint(
                    id=joint["id"],
                    type=joint["type"],
                    parent=joint["parent"],
                    child=joint["child"],
                    axis=(axis[0], axis[1], axis[2]),
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
        else:
            magnitude = float(mag)
        loads.append(
            Load(
                id=load["id"],
                kind=load["kind"],
                target=load["target"],
                magnitude=magnitude,
                units=load["units"],
                safety_factor=float(load["safety_factor"]),
                source=load["source"],
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
    return PrintSpec(
        schema_version=int(data["schema_version"]),
        part_name=nested(data, "part.name"),
        revision=nested(data, "part.revision"),
        product_class=nested(data, "part.product_class"),
        purpose=nested(data, "part.purpose"),
        process=nested(data, "manufacturing.process"),
        printer=nested(data, "manufacturing.printer"),
        build_volume_mm=(float(bx), float(by), float(bz)),
        material=nested(data, "manufacturing.material"),
        nozzle_mm=float(nested(data, "manufacturing.nozzle_mm")),
        layer_height_mm=float(nested(data, "manufacturing.layer_height_mm")),
        backend=nested(data, "cad.backend"),
        source_files=tuple(nested(data, "cad.source_files")),
        min_wall_mm=float(nested(data, "geometry.min_wall_mm")),
        min_feature_mm=float(nested(data, "geometry.min_feature_mm")),
        stl_files=bodies,
        fit_required=bool(nested(data, "fit.required")),
        clearance_per_side_mm=float(nested(data, "fit.clearance_per_side_mm")),
        fit_evidence=nested(data, "fit.evidence"),
        fit_coupon=coupon if isinstance(coupon, str) else None,
        dimensions=dimensions,
        orientation=nested(data, "print.orientation"),
        bed_face=nested(data, "print.bed_face"),
        up_axis=nested(data, "print.up_axis"),
        supports=nested(data, "print.supports"),
        max_overhang_deg=float(nested(data, "print.max_overhang_deg")),
        service_environment=nested(data, "service.environment"),
        drainage=nested(data, "service.drainage"),
        extra_parameters=extra_cad_parameters(data),
        hardware=tuple(hardware_comps),
        assembly_frame=assembly_frame if isinstance(assembly_frame, str) else None,
        assembly_bodies=tuple(assembly_bodies),
        joints=tuple(joints),
        loads=tuple(loads),
        sim_scene=sim_scene,
    )


def load_spec(
    path: Path, project: Path | None = None, check_files: bool = False
) -> tuple[PrintSpec | None, list[str]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"cannot parse {path}: {exc}"]
    errors = validate(data, project=project, check_files=check_files)
    if errors:
        return None, errors
    return parse_spec(data), []


def _source_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = _BLOCK_COMMENT.sub(" ", text)
    text = _LINE_COMMENT.sub(" ", text)
    if path.suffix == ".py":
        text = _HASH_COMMENT.sub(" ", text)
    return text


def parameter_declared(parameter: str, text: str) -> bool:
    if not parameter.isidentifier():
        return False
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(parameter)}\s*=", text) is not None


def parameters_in_sources(spec: PrintSpec, project: Path) -> list[str]:
    text = "\n".join(
        _source_text(project / rel)
        for rel in spec.source_files
        if (project / rel).is_file()
    )
    errors: list[str] = []
    seen: set[str] = set()
    for dim in spec.dimensions:
        seen.add(dim.parameter)
        if not parameter_declared(dim.parameter, text):
            errors.append(f"CAD parameter not found in declared source files: {dim.parameter}")
    for parameter in spec.extra_parameters:
        if parameter in seen:
            continue
        seen.add(parameter)
        if not parameter_declared(parameter, text):
            errors.append(f"CAD parameter not found in declared source files: {parameter}")
    return errors
