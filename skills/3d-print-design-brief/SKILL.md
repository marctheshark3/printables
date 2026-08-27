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
- Before selecting OpenSCAD, Blender, or an optional VibeCAD remake

Do not write CAD in this skill.

## Backend Decision

Choose exactly one:

- `openscad`: dimensional mechanical parts, exact fits, brackets, stands, mounts, enclosures
- `blender`: organic skins, sculpted surfaces, or lattices
- `hybrid`: separate declared dimensional and organic bodies; never two backends editing the same body
- `vibecad`: optional 10-X-eng/vibecad remake when the human is already in VibeCAD or asked to remake there; not the default for a new bracket

If uncertain, choose `openscad`.

## Procedure

1. Copy `templates/PRINT_SPEC.yaml` to `<project>/docs/PRINT_SPEC.yaml`.
2. Replace every example value. No placeholder may remain.
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
