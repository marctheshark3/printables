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
    "wet-fixture", "pip-hinge", "silhouette", "other",
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
            label = f"dimensions[{index}]"
            if not isinstance(dim, dict):
                errors.append(f"{label} must be a mapping")
                continue
            for key in ("name", "parameter", "value_mm", "tolerance_mm", "source"):
                if key not in dim:
                    errors.append(f"{label}.{key} is required")
            name = dim.get("name")
            if not isinstance(name, str) or not name:
                errors.append(f"{label}.name must be non-empty")
            elif name in names:
                errors.append(f"duplicate dimension name: {name}")
            else:
                names.add(name)
            parameter = dim.get("parameter")
            if not isinstance(parameter, str) or not parameter.isidentifier():
                errors.append(f"{label}.parameter must be a valid CAD identifier")
            for key in ("value_mm", "tolerance_mm"):
                if key in dim and (not finite_number(dim[key]) or float(dim[key]) < 0):
                    errors.append(f"{label}.{key} must be a finite non-negative number")
            if dim.get("source") not in DIMENSION_SOURCES:
                errors.append(f"{label}.source must be one of {sorted(DIMENSION_SOURCES)}")

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
    for dim in spec.dimensions:
        if not parameter_declared(dim.parameter, text):
            errors.append(f"CAD parameter not found in declared source files: {dim.parameter}")
    return errors
