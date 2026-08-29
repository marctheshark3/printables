---
name: 3d-print-reverse
description: Rebuild an STL as editable STEP and gated STL.
version: 1.0.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [3d-print, stl, step, reverse-engineering, brep]
    related_skills: [3d-print-design-brief, 3d-print-validate, 3d-print-openscad, 3d-print-vibecad]
---

# Reverse engineer STL → editable STEP

Rebuild an existing triangle mesh as an **editable B-rep**. The STL is a **reference only**. There is no automatic converter that produces a proper CAD file. Recreate the part with sketches and features so faces are selectable and parameters can change.

Do **not** convert triangles into STEP faces. **triangle-wrapped STEP is HARD.**

This skill is not in `/3d-print`. Reverse is a skill; the kernel is OCC (10-X-eng/vibecad or CadQuery). Do not invent `cad.backend: reverse`.

## When to Use

- User says reverse engineer this STL to STEP
- An existing mesh must become parametric millimetre CAD plus a gated STL
- Brackets, mounts, enclosures whose design intent is planes, cylinders, holes, fillets

**Don’t use for:** a new dimensional part from calipers (`3d-print-openscad`); organic lattice that would already be `cad.backend: blender` unless the organic flag is explicit.

## Hard sequence

```
1. preverse analyze   — import STL as reference; weld 1e-5 mm; AABB/PCA align; millimetres
2. preverse segment   — dihedral region grow; fit plane → cylinder → cone → sphere
3. preverse sketch    — planar sections; line/arc/circle; inner loops are holes
4. preverse features  — extrude / revolve / loft / hole / fillet / chamfer / mirror
5. preverse spec      — docs/PRINT_SPEC.yaml; cad.backend matches the kernel
6. preverse rebuild   — IR → src/<body>.py named millimetre parameters
7. preverse export    — millimetre AP214 STEP + binary STL (OCC kernel)
8. preverse compare   — two-sided deviation vs the input STL
9. preverse gate      — validate_print_spec + validate_project + deviation HARD
```

Agent one-liner:

```bash
preverse run --stl in.stl --project "$PROJECT"
```

PRINT_SPEC.yaml is the manufacturing contract. `reverse/<body>.ir.json` is the only rebuild input. Markdown cannot override it.

## Classify every STL. Never invent CAD.

| Class | When | What you ship |
|---|---|---|
| `parametric` | Feature IR rebuilds within `max_deviation_mm` | IR + PRINT_SPEC + CAD source + STEP + STL |
| `analytic` | Planes/cylinders/cones/spheres/tori fit; no feature tree | Fitted B-rep STEP + STL + report |
| `organic` | Only if a new part would already be `cad.backend: blender` | NURBS STEP + STL + explicit flag |
| `failed` | Illegal mesh or no class meets tolerance | JSON report only. **No** STEP/STL claim |

`parametric` is the default target for brackets, mounts, enclosures. Mixed classes per region must be listed. Silent mixed output is HARD.

## Kernels

OpenSCAD and Blender cannot emit editable STEP. Do not export STEP from them. Do not use `csg2stp`. Do not treat 10-X-eng/vibecad `mesh.to_shape` as reverse-engineered STEP — it is a faceted OCC snapshot, not design intent.

Detection for STEP export:

1. `--kernel vibecad` or `auto` + `VIBECAD_CMD`
2. `--kernel cadquery` or `auto` + `PREVERSE_STEP_IMAGE` (pinned digest, never `:latest`)
3. `PREVERSE_PYTHON` venv escape hatch
4. Else exit **2**. Never write a fake STEP.

Product kernel is **10-X-eng/vibecad** (OCC FreeCAD fork, not the PyPI package). CadQuery Docker is the CI STEP path when VibeCAD is absent. Host Python must not import `cadquery` or `FreeCAD` at CLI import time. Linux ARM qemu-x86_64 AppImage is unsupported. Do not enable VibeCAD MCP.

`cad.backend` is `vibecad` or `cadquery`, matching the rebuild source. Never lie with `openscad`.

## Proof

Deviation vs the **input** STL is the proof, not “this was the original CAD.” `reports/<body>.deviation.json` must have `max`, `mean`, `p95`, `n`, `max_deviation_mm`, `pass`. Fillet recovery is best-effort. Short STL chords stay warning-only.

## Scripts

```bash
SKILL=skills/3d-print-reverse
"$SKILL/scripts/preverse" analyze --stl in.stl --project "$PROJECT"
"$SKILL/scripts/preverse" run --stl in.stl --project "$PROJECT"
```

## Pitfalls

1. Triangle-wrapped STEP (face count ≥ 0.9 × input triangles)
2. Treating `mesh.to_shape` as success
3. Snapping dimensions without `--snap-mm`
4. Parsing DESIGN.md
5. Enabling VibeCAD MCP
6. Vendoring 10-X-eng/vibecad into this pack
7. Adding this skill to `/3d-print`
8. CadQuery `Plane.normal` = extrude direction (mirrors UV; use sketch x×y and a signed extrude)
9. Mapping AABB `width_mm×depth_mm` onto sketch UV when x_axis is not world X

## Verification

- [ ] `docs/PRINT_SPEC.yaml` passes `validate_print_spec.py`
- [ ] Parametric CAD source with named millimetre parameters
- [ ] `step/<body>.step` is analytic B-rep, or export exited 2
- [ ] `stl/<body>.stl` from that B-rep or the same IR; `validate_project.py` HARD=0
- [ ] `reports/<body>.deviation.json` max ≤ `max_deviation_mm`
- [ ] Same input bytes + flags → same IR/reports
