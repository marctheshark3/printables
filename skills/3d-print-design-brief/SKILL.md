---
name: 3d-print-design-brief
description: Define a validated FDM part contract before CAD.
version: 1.0.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [3d-print, fdm, design-contract, dimensions, tolerances]
    related_skills: [3d-print-openscad, 3d-print-blender, 3d-print-validate, 3d-print-vibecad]
---

# 3D Print Design Brief

Create `docs/PRINT_SPEC.yaml` before CAD. This file is the sole machine-readable manufacturing contract. Markdown may explain decisions but cannot override it.

## When to Use

- Any new or redesigned FDM part
- A part derived from a photo, sketch, existing STL, or measured object
- Before selecting VibeCAD, OpenSCAD, or Blender

Do not write CAD in this skill.

## Backend Decision

Choose exactly one:

- `vibecad`: dimensional mechanical parts, exact fits, brackets, stands, mounts, enclosures using 10-X-eng/vibecad
- `openscad`: a request naming OpenSCAD, CI sample exports, or a host where VibeCAD cannot run
- `blender`: organic skins, sculpted surfaces, or lattices
- `hybrid`: separate declared dimensional and organic bodies; never two backends editing the same body
- `cadquery`: optional analytic STEP reconstruction through `3d-print-reverse`

VibeCAD is the dimensional kernel. Honor an explicit OpenSCAD request. Blender remains for organic or lattice bodies. Use the 10-X-eng project, not the PyPI package named vibecad or upstream FreeCAD.

## Procedure

1. Copy `templates/PRINT_SPEC.yaml` to `<project>/docs/PRINT_SPEC.yaml`.
2. Replace every example value, including the backend and source paths when another backend is selected. No placeholder may remain.
3. Record each critical dimension with:
   - stable parameter name
   - nominal `value_mm`
   - `tolerance_mm`
   - provenance: `measured`, `from-user`, `datasheet`, `fit-tested`, or `assumed`
4. Express clearance as `clearance_per_side_mm`, never total clearance.
5. Declare one output entry per independently manufactured body and its `expected_shells`. An assembly is several entries.
6. Lock bed face, Z-up orientation, support policy, material, nozzle, minimum wall, and minimum feature.
7. Run through `terminal`:

```bash
python3 scripts/validate_print_spec.py <project>/docs/PRINT_SPEC.yaml
```

Proceed to CAD only when it exits zero.

## After a printed coupon

When `fit.required` is true, generate the coupon before it is printed:

```bash
python3 scripts/generate_coupon.py <project>
```

After that coupon is printed, write the caliper reading the user measured. Missing `--measured-mm` exits without changing the file.

```bash
python3 scripts/record_fit.py <project> --parameter <name> --measured-mm <caliper>
python3 scripts/validate_print_spec.py <project>/docs/PRINT_SPEC.yaml
```

The write sets that dimension's `source` to `fit-tested` and stores the reading on `fit.measured_mm`. Pass `--keep-nominal` only when the nominal must stay. Field rules stay in `references/print-spec-v1.md`.

## Hard Rules

- `cad.parametric: true`
- units are millimetres and print-up is Z
- `overlapping_solids_allowed: false`
- one STL per independently manufactured body
- assumed critical fits do not ship
- minimum wall and feature are at least two nozzle widths
- wet parts require drainage and non-PLA material

Read `references/print-spec-v1.md` for field semantics.

## Pitfalls

- Treating a photograph as a caliper
- Naming a dimension without mapping it to a CAD parameter
- Writing “0.8 mm clearance” without saying per-side or total
- Combining separately printed bodies into one STL
- Choosing a backend because it is novel

## Verification

- [ ] `docs/PRINT_SPEC.yaml` exists
- [ ] contract validator exits zero
- [ ] every output body and shell count is declared
- [ ] every critical dimension has tolerance and provenance
- [ ] backend is selected by geometry need
