#!/usr/bin/env python3
"""Validate PRINT_SPEC.yaml and every declared STL in-process."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BRIEF_SCRIPTS = SCRIPTS.parent.parent / "3d-print-design-brief" / "scripts"
for path in (str(SCRIPTS), str(BRIEF_SCRIPTS)):
    if path not in sys.path:
        sys.path.insert(0, path)

from print_spec import load_spec, parameters_in_sources  # noqa: E402
from validate_stl import audit_mesh, report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an FDM project fail-closed")
    parser.add_argument("project", type=Path)
    parser.add_argument("--spec", default="docs/PRINT_SPEC.yaml")
    args = parser.parse_args()

    project = args.project.resolve()
    spec, errors = load_spec(project / args.spec, project=project, check_files=True)
    if spec is not None:
        errors.extend(parameters_in_sources(spec, project))
    if spec is None or errors:
        for error in errors:
            print(f"HARD: {error}")
        print(f"RESULT: FAIL ({len(errors)} contract/source errors)")
        return 1

    failures = 0
    for body in spec.stl_files:
        stl = project / body.path
        print(f"=== {body.body}: {body.path} ===")
        hard, warn, info = audit_mesh(
            stl,
            expected_shells=body.expected_shells,
            build=spec.build_volume_mm,
            product_class=spec.product_class,
            orientation=spec.orientation,
            up_axis=spec.up_axis,
            min_feature_mm=spec.min_feature_mm,
            min_wall_mm=spec.min_wall_mm,
            max_overhang_deg=spec.max_overhang_deg,
        )
        report(hard, warn, info)
        if hard:
            failures += 1

    if failures:
        print(f"RESULT: FAIL ({failures} STL files failed)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
