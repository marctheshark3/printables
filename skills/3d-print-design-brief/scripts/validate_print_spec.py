#!/usr/bin/env python3
"""Fail-closed validation for docs/PRINT_SPEC.yaml."""
from __future__ import annotations

import argparse
import math
import sys
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
DIMENSION_SOURCES = {"measured", "from-user", "datasheet", "fit-tested", "assumed"}
SUPPORT_POLICIES = {"none", "build-plate-only", "required"}
SERVICE_ENVIRONMENTS = {"dry", "wet"}


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


def validate(data: Any, project: Path | None = None, check_files: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be a mapping"]

    required = [
        "schema_version", "part.name", "part.revision", "part.product_class", "part.purpose",
        "manufacturing.process", "manufacturing.printer", "manufacturing.build_volume_mm", "manufacturing.material",
        "manufacturing.nozzle_mm", "manufacturing.layer_height_mm",
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
    if not isinstance(source_files, list) or not source_files or not all(isinstance(x, str) and safe_relative_path(x) for x in source_files):
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
    if nested(data, "fit.required") is True:
        if evidence in {"assumed", "none"}:
            errors.append("required fit needs measured, from-user, datasheet, or fit-tested evidence")
        coupon = data.get("fit", {}).get("coupon")
        if evidence != "fit-tested" and not coupon:
            errors.append("required fit needs fit.coupon unless evidence is fit-tested")
    elif nested(data, "fit.required") is not False:
        errors.append("fit.required must be true or false")

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
        if nested(data, "service.drainage") in {"none", "not-applicable", "unspecified"}:
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
        for rel in paths:
            if not safe_relative_path(rel):
                continue
            p = project / rel
            if not p.is_file():
                errors.append(f"declared file does not exist: {rel}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate printable part contract")
    parser.add_argument("spec", type=Path)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--check-files", action="store_true")
    args = parser.parse_args()
    try:
        data = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"HARD: cannot parse {args.spec}: {exc}")
        return 1
    project = args.project or args.spec.parent.parent
    errors = validate(data, project=project, check_files=args.check_files)
    if errors:
        for error in errors:
            print(f"HARD: {error}")
        print(f"RESULT: FAIL ({len(errors)} errors)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
