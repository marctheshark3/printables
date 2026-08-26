---
name: 3d-print-blender
description: Build organic or lattice FDM parts in Blender.
version: 1.0.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [3d-print, fdm, blender, bpy, lattice, organic]
    related_skills: [3d-print-design-brief, 3d-print-validate, 3d-print-openscad]
---

# 3D Print Blender

Build organic, sculpted, or lattice FDM bodies using parameterized `bpy` scripts. Blender is an exception backend, not the dimensional default.

## When to Use

Use only when `cad.backend: blender`, or for the Blender-owned body of `cad.backend: hybrid`.

Use OpenSCAD for precise brackets, ports, bosses, stands, and mating shells.

## Source Contract

- headless `bpy` script is the source of truth
- all dimensions and cleanup settings are named parameters
- units are millimetres, Z-up
- one scene object per independently printed body at export
- modifiers are applied deterministically
- boolean operands are removed before export
- exported mesh has no duplicate, internal, non-manifold, or self-intersecting geometry

## Procedure

1. Validate `docs/PRINT_SPEC.yaml`.
2. Confirm the requested body is organic or lattice; otherwise hand off to `3d-print-openscad`.
3. Use `scripts/pblend new` for the project scaffold.
4. Implement the body in `src/build.py` using named parameters.
5. Run:

```bash
scripts/pblend run --project "$PROJECT"
scripts/pblend preview --project "$PROJECT"
scripts/pblend gate --project "$PROJECT"
```

`pblend gate` resolves `3d-print-validate/scripts/validate_project.py`. Override with `PRINT_VALIDATOR`. `DFM_GATE` is accepted as a deprecated alias.

6. Inspect separate print-orientation stills. A malformed still blocks delivery even if mesh checks pass.
7. Run the backend-neutral `3d-print-validate` contract and STL checks.

## Pitfalls

- Voxel remesh can destroy ports and fit surfaces
- a manifold modifier can hide a bad modeling sequence
- joined objects are not necessarily unioned solids
- an assembly preview does not prove each printable body
- host Python cannot import `bpy`; run through Blender

## Verification

- [ ] backend choice is justified by organic or lattice geometry
- [ ] parameterized `bpy` source exists
- [ ] temporary operands are absent from export
- [ ] each STL matches its declared shell count
- [ ] separate stills pass visual inspection
- [ ] `3d-print-validate` reports HARD=0
