---
name: 3d-print-openscad
description: Build parametric dimensional FDM parts in OpenSCAD.
version: 1.0.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [3d-print, fdm, openscad, parametric, mechanical-cad]
    related_skills: [3d-print-design-brief, 3d-print-validate]
---

# 3D Print OpenSCAD

Build dimensional mechanical FDM parts from a validated `docs/PRINT_SPEC.yaml`. OpenSCAD is the default backend for brackets, mounts, stands, trays, enclosures, and exact interfaces.

## When to Use

Use when `cad.backend: openscad`, or when the geometry is dimensional and no backend has been selected.

Do not use for sculpted organic surfaces or decorative lattices; use `3d-print-blender`. A VibeCAD remake is `3d-print-vibecad` only when the human is already in VibeCAD or asked to remake there — not the default for a new bracket.

## Source Contract

- one named parameter for every dimension in `PRINT_SPEC.yaml`
- parameters grouped at the top of the source
- millimetres only
- no unexplained numeric literals in geometry modules
- one module per printable body
- booleans produce final bodies; overlapping primitives are construction inputs, never exported bodies
- each output body renders alone for export

## Procedure

1. Run the print-spec validator. Stop on non-zero exit.
2. Start from the matching class template under `templates/`.
3. Implement named parameters and assertions for invalid ranges.
4. Build one final manifold body per STL.
5. Export with pinned OpenSCAD:

```bash
docker run --rm -v "$PROJECT:/work" -w /work \
  openscad/openscad:2021.01 \
  openscad -o /work/stl/<body>.stl --export-format=binstl /work/src/<part>.scad
```

6. Run `3d-print-validate` on the project. HARD fail means redesign and re-export.
7. Render each body in print orientation plus an underside view. Visual defects block delivery.

## Geometry Rules

- minimum wall and feature come from the spec
- use per-side clearance from the spec
- grow geometry from the bed face; avoid unsupported starts
- screw and connector interfaces use measured or datasheet dimensions
- connector window defaults live in `references/connector-keepouts-fdm.md`
- heat-set insert OD/hole/boss defaults live in `references/heat-set-inserts-fdm.md`; printed thread is opt-in only
- independent bodies do not touch or overlap in exported mode
- no zero-thickness contact, coincident faces, or decorative internal geometry

## Pitfalls

- A successful OpenSCAD render does not prove a watertight STL
- `union()` around intersecting bodies is not proof they became one shell
- `$fn` tessellation density is not wall thickness
- preview mode can hide CGAL failures; validate the exported binary STL

## Verification

- [ ] print spec passes
- [ ] all dimensions map to named parameters
- [ ] one exported STL per declared body
- [ ] backend validator reports valid final solid count
- [ ] `3d-print-validate` reports HARD=0
- [ ] print-orientation renders look intentional
