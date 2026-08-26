#!/usr/bin/env python3
"""Place assembled STLs and hardware envelopes; fail closed on occupancy, sweep, loads."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BRIEF_SCRIPTS = SCRIPTS.parent.parent / "3d-print-design-brief" / "scripts"
for path in (str(SCRIPTS), str(BRIEF_SCRIPTS)):
    if path not in sys.path:
        sys.path.insert(0, path)

from assembly import audit_assembly  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate assembled occupancy fail-closed")
    parser.add_argument("project", type=Path)
    parser.add_argument("--spec", default="docs/PRINT_SPEC.yaml")
    args = parser.parse_args()

    project = args.project.resolve()
    hard, warn, info = audit_assembly(project, spec_rel=args.spec)
    for line in info:
        print(f"INFO: {line}")
    for line in warn:
        print(f"WARN: {line}")
    for line in hard:
        print(f"HARD: {line}")
    if hard:
        print(f"RESULT: FAIL ({len(hard)} errors)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
