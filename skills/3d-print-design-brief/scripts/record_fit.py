#!/usr/bin/env python3
"""Record a caliper measurement onto PRINT_SPEC.yaml. Never invent a value."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    raise SystemExit("HARD: PyYAML is required: python3 -m pip install PyYAML") from exc

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from print_spec import load_spec  # noqa: E402


def find_dimension(data: dict, parameter: str) -> dict | None:
    dims = data.get("dimensions")
    if not isinstance(dims, list):
        return None
    for dim in dims:
        if isinstance(dim, dict) and dim.get("parameter") == parameter:
            return dim
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a measured fit back into PRINT_SPEC")
    parser.add_argument("project", type=Path)
    parser.add_argument("--parameter", required=True)
    parser.add_argument("--measured-mm", type=float, default=None)
    parser.add_argument("--keep-nominal", action="store_true")
    args = parser.parse_args()
    if args.measured_mm is None:
        print("HARD: --measured-mm is required; will not invent a measurement")
        return 1

    project = args.project.resolve()
    spec_path = project / "docs" / "PRINT_SPEC.yaml"
    spec, errors = load_spec(spec_path, project=project)
    if spec is None or errors:
        for error in errors:
            print(f"HARD: {error}")
        return 1
    if args.parameter not in {dim.parameter for dim in spec.dimensions}:
        print(f"HARD: parameter not in PRINT_SPEC dimensions: {args.parameter}")
        return 1

    data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    dim = find_dimension(data, args.parameter)
    if dim is None:
        print(f"HARD: parameter not in PRINT_SPEC dimensions: {args.parameter}")
        return 1
    dim["source"] = "fit-tested"
    if not args.keep_nominal:
        dim["value_mm"] = float(args.measured_mm)
    fit = data.setdefault("fit", {})
    if not isinstance(fit, dict):
        print("HARD: fit must be a mapping")
        return 1
    measured = fit.setdefault("measured_mm", {})
    if not isinstance(measured, dict):
        print("HARD: fit.measured_mm must be a mapping")
        return 1
    measured[args.parameter] = float(args.measured_mm)
    spec_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print(f"FIT: {args.parameter}={args.measured_mm} source=fit-tested")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
