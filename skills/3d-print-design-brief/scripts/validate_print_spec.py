#!/usr/bin/env python3
"""CLI: validate one docs/PRINT_SPEC.yaml."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from print_spec import load_spec


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate printable part contract")
    parser.add_argument("spec", type=Path)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--check-files", action="store_true")
    args = parser.parse_args()
    project = args.project or args.spec.parent.parent
    _spec, errors = load_spec(args.spec, project=project, check_files=args.check_files)
    if errors:
        for error in errors:
            print(f"HARD: {error}")
        print(f"RESULT: FAIL ({len(errors)} errors)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
