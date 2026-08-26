---
name: 3d-print-validate
description: Fail closed on printable-part specs and STL geometry.
version: 1.0.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [3d-print, fdm, validation, stl, manifold, watertight]
    related_skills: [3d-print-design-brief, 3d-print-openscad, 3d-print-blender]
---

# 3D Print Validate

Validate the machine-readable print contract and every exported STL. This skill is backend-neutral. It does not assume OpenSCAD, Blender, VibeCAD, or FreeCAD.

## When to Use

- after every STL export
- after changing any CAD parameter
- before saying a part is printable or delivering files
- when evaluating a new CAD backend

## Procedure

Run one command after export:

```bash
python3 scripts/validate_project.py "$PROJECT"
```

It validates `docs/PRINT_SPEC.yaml`, confirms every declared source/output file exists, confirms each dimension maps to a named CAD parameter, and runs the STL gate for every declared body with the spec's X/Y/Z build volume and shell count.

Never convert a HARD check into a warning to make a file pass.

## Hard Checks

- contract complete and internally consistent
- source and output files exist
- STL parses and has positive volume
- closed watertight topology
- no boundary or non-manifold edges
- consistent face orientation
- no duplicate or excessive degenerate faces
- edge-connected shell count equals `expected_shells`
- overlapping exported solids are rejected
- bounding box fits strictly inside the printer envelope
- fit and wet-service evidence are acceptable
- overhang and class-specific rules pass

Short STL chords are tessellation, not a wall-thickness measurement. Chord density is warning-only. Minimum walls are verified from CAD parameters and slicer output.

## Overrides

Only the user may waive a named check. Record the exact check, reason, and scope in `PRINT_SPEC.yaml`. Never use a global “ignore validation” switch.

## Verification

- [ ] spec validator exits zero
- [ ] every declared STL was checked
- [ ] every STL is watertight and has the expected shell count
- [ ] backend solid validity was checked before export
- [ ] HARD=0 or each named override is user-approved and recorded
