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

Prove the CAD/CAM contract and every exported body. Backend-neutral. Does not parse DESIGN.md.

## When to Use

- after every STL export
- after changing any CAD parameter
- before saying a part is printable or delivering files
- when an assembly has more than one independently manufactured body

## Procedure

```bash
python3 scripts/validate_project.py "$PROJECT"
```

That command:

1. loads `docs/PRINT_SPEC.yaml` (fit, drainage, material, parameters, bodies)
2. checks declared source/STL/coupon files exist
3. checks each dimension maps to a CAD assignment
4. audits each STL in-process (topology, occupancy, volume, envelope, DFM)

Never convert a HARD check into a warning to make a file pass.

When `assembly` is present, run the occupancy gate after mesh validation:

```bash
python3 scripts/validate_assembly.py "$PROJECT"
```

That command places printed STLs and hardware envelopes at declared poses and fail-closes on illegal collision, joint self-collision, and missing or assumed required loads. A render is not proof. Mesh HARD gates stay required.

Mesh-only (no spec policy):

```bash
python3 scripts/validate_stl.py --stl path.stl --build-x-mm 256 --build-y-mm 256 --build-z-mm 256 \
  --expected-components 1 --product-class bracket --print-orientation base-on-bed
```

## Hard Checks

Spec (this skill consumes `3d-print-design-brief`):

- contract complete and internally consistent
- source, output, and coupon files exist
- fit and wet-service evidence are acceptable
- CAD parameters are declared, not mentioned

Mesh:

- STL parses and has positive signed volume
- closed watertight topology
- no boundary or non-manifold edges
- consistent face orientation
- no duplicate or excessive degenerate faces
- edge-connected shell count equals `expected_shells`
- overlapping exported solids are rejected
- bounding box fits strictly inside the machine envelope
- overhang and class-specific rules pass

Short STL chords are tessellation, not wall thickness. Chord density is warning-only.

## Overrides

Only the user may waive a named check. Record the exact check, reason, and scope in `PRINT_SPEC.yaml`.

## Verification

- [ ] spec validator exits zero
- [ ] every declared STL was checked
- [ ] every STL is watertight and has the expected shell count
- [ ] backend solid validity was checked before export
- [ ] HARD=0 or each named override is user-approved and recorded
