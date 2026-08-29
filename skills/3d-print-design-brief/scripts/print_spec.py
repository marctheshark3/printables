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


BACKENDS = {"openscad", "blender", "hybrid", "vibecad", "cadquery"}
VIBECAD_PARAMETRIC_SUFFIXES = {".py", ".vibescript"}
VIBECAD_NON_PARAMETRIC_SUFFIXES = {".fcstd", ".md", ".markdown"}
CADQUERY_PARAMETRIC_SUFFIXES = {".py"}
REVERSE_CLASSES = {"parametric", "analytic", "organic", "failed"}
REVERSE_KERNEL_BACKENDS = {"vibecad", "cadquery"}
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
PRINTER_IDENTITY_KEYS = {
    "ip", "printer_ip", "lan_ip", "access_code", "serial", "host", "mqtt_password",
}
_INSERT_OD = re.compile(
    r"(insert|heat_set|heatset).*(od|outer|diameter|dia)|"
    r"(od|outer|diameter|dia).*(insert|heat_set|heatset)",
    re.I,
)
CRITICAL_HARDWARE_ROLES = {"mcu", "servo", "motor", "drive"}
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
    magnitude_xyz: tuple[float, float, float] | None = None
    section_outer: str | None = None
    section_inner: str | None = None


@dataclass(frozen=True)
class SimScene:
    id: str
    gravity_mm_s2: tuple[float, float, float]
    floor_z_mm: float
    friction_mu: float
    friction_source: str


@dataclass(frozen=True)
class CalibrationCoupon:
    id: str
    type: str
    source: str
    magnitude: float
    units: str
    target: str | None
    scene: str | None
    actuator_kind: str | None


@dataclass(frozen=True)
class SimRoll:
    distance_mm: float
    scene: str
    sim_mm: float | None
    bench_mm: float | None
    error_budget_mm: float | None
    source: str | None


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
    sim2real: bool
    calibration: tuple[CalibrationCoupon, ...]
    sim_roll: SimRoll | None
    pack_required: bool = False
    slice_process_card: str | None = None
    slice_three_mf: str | None = None
    fit_measured_mm: tuple[tuple[str, float], ...] = ()


@dataclass(frozen=True)
class OptionalBlocks:
    hardware: tuple[HardwareComponent, ...]
    assembly_frame: str | None
    assembly_bodies: tuple[AssemblyBody, ...]
    joints: tuple[AssemblyJoint, ...]
    loads: tuple[Load, ...]
    sim_scene: SimScene | None
    sim2real: bool
    calibration: tuple[CalibrationCoupon, ...]
    sim_roll: SimRoll | None


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


def vibecad_source_suffix(path: str) -> str:
    return Path(path).suffix.lower()


def vibecad_has_parametric_source(source_files: Any) -> bool:
    if not isinstance(source_files, list) or not source_files:
        return False
    suffixes = [
        vibecad_source_suffix(item) for item in source_files if isinstance(item, str)
    ]
    if not suffixes:
        return False
    if all(suffix in VIBECAD_NON_PARAMETRIC_SUFFIXES for suffix in suffixes):
        return False
    return any(suffix in VIBECAD_PARAMETRIC_SUFFIXES for suffix in suffixes)


def is_insert_od_dimension(name: str, parameter: str) -> bool:
    blob = f"{name} {parameter}".replace("-", "_")
    return _INSERT_OD.search(blob) is not None


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


def validate_reverse(data: dict[str, Any], errors: list[str]) -> None:
    reverse = data.get("reverse")
    if reverse is None:
        return
    if not isinstance(reverse, dict):
        errors.append("reverse must be a mapping")
        return
    klass = reverse.get("class")
    if klass is not None and klass not in REVERSE_CLASSES:
        errors.append(f"reverse.class must be one of {sorted(REVERSE_CLASSES)}")
    backend = nested(data, "cad.backend")
    if klass == "organic":
        if backend != "blender":
            errors.append("reverse.class organic requires cad.backend blender")
    elif backend not in REVERSE_KERNEL_BACKENDS:
        errors.append(
            "reverse projects require cad.backend vibecad or cadquery; never openscad"
        )
    for key in ("input_stl", "ir"):
        rel = reverse.get(key)
        if rel is None:
            continue
        if not isinstance(rel, str) or not safe_relative_path(rel):
            errors.append(f"reverse.{key} must be a project-relative path without '..'")
    max_dev = reverse.get("max_deviation_mm")
    if max_dev is not None and (not finite_number(max_dev) or float(max_dev) < 0):
        errors.append("reverse.max_deviation_mm must be a finite non-negative number")
    step_files = reverse.get("step_files")
    if step_files is None:
        return
    if not isinstance(step_files, list):
        errors.append("reverse.step_files must be a list")
        return
    for index, item in enumerate(step_files):
        label = f"reverse.step_files[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be a mapping")
            continue
        path = item.get("path")
        if not isinstance(path, str) or not safe_relative_path(path):
            errors.append(f"{label}.path must be project-relative and cannot contain '..'")
        if "body" in item and (not isinstance(item.get("body"), str) or not item.get("body")):
            errors.append(f"{label}.body must be non-empty")


from print_spec_assembly import (  # noqa: E402
    parse_optional_blocks,
    validate_assembly,
    validate_loads,
    validate_sim,
)


def validate_printer_identity(data: dict[str, Any], errors: list[str]) -> None:
    manufacturing = data.get("manufacturing")
    if not isinstance(manufacturing, dict):
        return
    for key in manufacturing:
        if str(key).lower() in PRINTER_IDENTITY_KEYS:
            errors.append(
                "manufacturing must not contain printer identity "
                "(IP, serial, access_code, host)"
            )
            return


def validate_pack_slice(data: dict[str, Any], errors: list[str]) -> None:
    pack = data.get("pack")
    if pack is not None:
        if not isinstance(pack, dict):
            errors.append("pack must be a mapping")
        else:
            required = pack.get("required")
            if required is not None and required not in (True, False):
                errors.append("pack.required must be true or false")
    slice_block = data.get("slice")
    if slice_block is None:
        return
    if not isinstance(slice_block, dict):
        errors.append("slice must be a mapping")
        return
    for key in ("process_card", "three_mf"):
        rel = slice_block.get(key)
        if rel is None:
            continue
        if not isinstance(rel, str) or not safe_relative_path(rel):
            errors.append(f"slice.{key} must be a project-relative path without '..'")


def validate_fit_measured(data: dict[str, Any], errors: list[str]) -> None:
    fit = data.get("fit")
    if not isinstance(fit, dict):
        return
    measured = fit.get("measured_mm")
    if measured is None:
        return
    if not isinstance(measured, dict):
        errors.append("fit.measured_mm must be a mapping of parameter to millimetres")
        return
    for key, value in measured.items():
        if not isinstance(key, str) or not key.isidentifier():
            errors.append("fit.measured_mm keys must be CAD parameter identifiers")
        if not finite_number(value) or float(value) < 0:
            errors.append(f"fit.measured_mm.{key} must be a finite non-negative number")


def validate_insert_od(data: dict[str, Any], errors: list[str]) -> None:
    try:
        fit_required = nested(data, "fit.required") is True
    except KeyError:
        return
    if not fit_required:
        return
    dimensions = data.get("dimensions")
    if isinstance(dimensions, list):
        for index, dim in enumerate(dimensions):
            if not isinstance(dim, dict):
                continue
            name = dim.get("name") if isinstance(dim.get("name"), str) else ""
            parameter = dim.get("parameter") if isinstance(dim.get("parameter"), str) else ""
            if dim.get("source") == "assumed" and is_insert_od_dimension(name, parameter):
                errors.append(
                    f"assumed insert OD cannot ship when fit.required: dimensions[{index}]"
                )
    hardware = data.get("hardware")
    components = hardware.get("components") if isinstance(hardware, dict) else None
    if not isinstance(components, list):
        return
    for c_index, comp in enumerate(components):
        if not isinstance(comp, dict):
            continue
        interfaces = comp.get("interfaces")
        if not isinstance(interfaces, list):
            continue
        for i_index, iface in enumerate(interfaces):
            if not isinstance(iface, dict):
                continue
            name = iface.get("name") if isinstance(iface.get("name"), str) else ""
            parameter = iface.get("parameter") if isinstance(iface.get("parameter"), str) else ""
            if iface.get("source") == "assumed" and is_insert_od_dimension(name, parameter):
                errors.append(
                    "assumed insert OD cannot ship when fit.required: "
                    f"hardware.components[{c_index}].interfaces[{i_index}]"
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
    elif nested(data, "cad.backend") == "vibecad" and not vibecad_has_parametric_source(source_files):
        errors.append(
            "cad.backend vibecad requires project-relative Python/VibeScript "
            "(.py or .vibescript); .FCStd and Markdown cannot be the only sources"
        )
    elif nested(data, "cad.backend") == "cadquery":
        suffixes = [
            vibecad_source_suffix(item) for item in source_files if isinstance(item, str)
        ]
        if not any(suffix in CADQUERY_PARAMETRIC_SUFFIXES for suffix in suffixes):
            errors.append(
                "cad.backend cadquery requires project-relative Python (.py) source"
            )

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
    validate_reverse(data, errors)
    validate_printer_identity(data, errors)
    validate_pack_slice(data, errors)
    validate_fit_measured(data, errors)
    validate_insert_od(data, errors)

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
        slice_block = data.get("slice")
        if isinstance(slice_block, dict):
            for key in ("process_card", "three_mf"):
                rel = slice_block.get(key)
                if isinstance(rel, str) and safe_relative_path(rel):
                    paths.append(rel)
        reverse = data.get("reverse")
        if isinstance(reverse, dict):
            for key in ("input_stl", "ir"):
                rel = reverse.get(key)
                if isinstance(rel, str) and safe_relative_path(rel):
                    paths.append(rel)
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
    extra = parse_optional_blocks(data)
    pack = data.get("pack") if isinstance(data.get("pack"), dict) else {}
    slice_block = data.get("slice") if isinstance(data.get("slice"), dict) else {}
    measured_raw = data.get("fit", {}).get("measured_mm") if isinstance(data.get("fit"), dict) else None
    measured: tuple[tuple[str, float], ...] = ()
    if isinstance(measured_raw, dict):
        measured = tuple(
            (str(key), float(value))
            for key, value in measured_raw.items()
            if isinstance(key, str) and finite_number(value)
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
        hardware=extra.hardware,
        assembly_frame=extra.assembly_frame,
        assembly_bodies=extra.assembly_bodies,
        joints=extra.joints,
        loads=extra.loads,
        sim_scene=extra.sim_scene,
        sim2real=extra.sim2real,
        calibration=extra.calibration,
        sim_roll=extra.sim_roll,
        pack_required=bool(pack.get("required", False)),
        slice_process_card=slice_block.get("process_card")
        if isinstance(slice_block.get("process_card"), str)
        else None,
        slice_three_mf=slice_block.get("three_mf")
        if isinstance(slice_block.get("three_mf"), str)
        else None,
        fit_measured_mm=measured,
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
