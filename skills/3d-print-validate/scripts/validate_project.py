#!/usr/bin/env python3
"""Validate one PRINT_SPEC.yaml and every declared STL."""
from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


SKILL_ROOT = Path(__file__).resolve().parents[1]
SPEC_VALIDATOR = SKILL_ROOT.parent / "3d-print-design-brief" / "scripts" / "validate_print_spec.py"
_spec = importlib.util.spec_from_file_location("print_spec_validator", SPEC_VALIDATOR)
if _spec is None or _spec.loader is None:
    raise SystemExit(f"HARD: cannot load {SPEC_VALIDATOR}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
validate = _module.validate


def mode_text(data: dict, expected_shells: int) -> str:
    fit = data["fit"]
    service = data["service"]
    manufacturing = data["manufacturing"]
    print_spec = data["print"]
    lines = {
        "product_class": data["part"]["product_class"],
        "print_orientation": print_spec["orientation"],
        "print_up_axis": print_spec["up_axis"],
        "min_feature_mm": data["geometry"]["min_feature_mm"],
        "overhang_max_deg": print_spec["max_overhang_deg"],
        "expected_components": expected_shells,
        "fit_required": "yes" if fit["required"] else "no",
        "critical_fit_status": fit["evidence"],
        "service_environment": service["environment"],
        "drainage": service["drainage"],
        "material": manufacturing["material"],
    }
    body = "\n".join(f"{key}: {value}" for key, value in lines.items())
    return f"---\n{body}\n---\n"


_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_LINE_COMMENT = re.compile(r"//.*?$", re.M)
_HASH_COMMENT = re.compile(r"#.*?$", re.M)


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


def parameters_in_sources(data: dict, project: Path) -> list[str]:
    errors: list[str] = []
    text = "\n".join(
        _source_text(project / rel)
        for rel in data["cad"]["source_files"]
        if (project / rel).is_file()
    )
    for dim in data["dimensions"]:
        parameter = dim["parameter"]
        if not parameter_declared(parameter, text):
            errors.append(f"CAD parameter not found in declared source files: {parameter}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an FDM project fail-closed")
    parser.add_argument("project", type=Path)
    parser.add_argument("--spec", default="docs/PRINT_SPEC.yaml")
    args = parser.parse_args()

    project = args.project.resolve()
    spec_path = project / args.spec
    try:
        data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"HARD: cannot parse {spec_path}: {exc}")
        return 1

    errors = validate(data, project=project, check_files=True)
    errors.extend(parameters_in_sources(data, project) if not errors else [])
    if errors:
        for error in errors:
            print(f"HARD: {error}")
        print(f"RESULT: FAIL ({len(errors)} contract/source errors)")
        return 1

    build_x, build_y, build_z = data["manufacturing"]["build_volume_mm"]
    validator = Path(__file__).with_name("validate_stl.py")
    failures = 0
    for output in data["geometry"]["stl_files"]:
        stl = project / output["path"]
        print(f"=== {output['body']}: {output['path']} ===")
        with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8") as mode:
            mode.write(mode_text(data, output["expected_shells"]))
            mode.flush()
            command = [
                sys.executable, str(validator),
                "--project", str(project),
                "--stl", str(stl),
                "--mode-file", mode.name,
                "--expected-components", str(output["expected_shells"]),
                "--build-x-mm", str(build_x),
                "--build-y-mm", str(build_y),
                "--build-z-mm", str(build_z),
            ]
            result = subprocess.run(command, check=False)
            if result.returncode:
                failures += 1

    if failures:
        print(f"RESULT: FAIL ({failures} STL files failed)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
