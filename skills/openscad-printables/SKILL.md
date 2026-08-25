---
name: openscad-printables
description: "Use when designing parametric OpenSCAD to STL parts for Bambu Lab P1S, including stands, mounts, enclosures, hinges, and wet fixtures. Requires locked intent and fit evidence, Docker export, welded-edge topology, component-count and DFM gates. Prefer the /printables bundle."
license: MIT
metadata:
  version: "4.1.0"
  author: Tron
  platforms: linux
  hermes:
    tags: [openscad, 3d-print, stl, bambu, p1s, cad, parametric, dfm, open-frame, printables]
    related_skills: [printables-part-brief, printables-dfm-gate, define-goal]
    regression_fixture: "~/Documents/the-grid/dgx-spark-stand"
---

# OpenSCAD Printables v4.1 — CAD step of the manufacturing loop

## Overview

Write **parametric OpenSCAD** and export manifold **STL** for **Bambu Lab P1S**. This is step 2 of:

1. **`printables-part-brief`** → `docs/DESIGN.md` intent (text + optional image)  
2. **`openscad-printables`** → this skill  
3. **`printables-dfm-gate`** → fail-closed mesh/mode gates  

Prefer **`/printables`** so all three load. **No CAD before intent card.**

Path: `.scad` → Docker `openscad/openscad:2021.01` → `validate_export.sh` / `dfm_gate.py` → previews → zip STL.

### Regression fixture

`~/Documents/the-grid/dgx-spark-stand/` — active gold **v10**. Skill changes must not break:

```bash
scripts/validate_export.sh ~/Documents/the-grid/dgx-spark-stand v10
```

## When to Use

- Intent card exists (or you just wrote it via part-brief)
- Mechanical FDM parts: stands, frames, mounts, wet fixtures, enclosures, PIP hinges
- Soft / open-frame / stackable / TOP-FIRST redesigns

**Don’t:** invent product class in SCAD without DESIGN.md; ship without DFM gates.

## Hard sequence

```
0. Require docs/DESIGN.md with product class, orientation, expected components, and fit provenance
1. Scaffold project: scripts/new_part.sh <name> <class>  OR use existing the-grid dir
2. Copy class template → src/<part>.scad (see map)
3. Parametric geometry; echo version / orientation / clearance / class every design
4. Docker export (export_stl.sh or validate_export.sh)
5. Run printables-dfm-gate (validate_export wires dfm_gate.py) — topology, components, fit, and DFM HARD fail = not done
6. Solid multi-view + under/cutaway; ghost chassis if equipment
7. Print notes + zip STL (Discord MEDIA zip, not raw STL)
```

## Product class → template

| product_class (from DESIGN.md) | Template |
|--------------------------------|----------|
| `equipment-open-frame` | `templates/open_frame_equipment_scaffold.scad` |
| `tray` | `templates/soft_part_scaffold.scad` |
| `pip-hinge` | `templates/pip_hinge_cones.scad` |
| `generative` | `templates/generative_loadpath.scad` (not under gear seating) |
| `bracket` / `wet-fixture` / `enclosure` / `other` | `templates/part_scaffold.scad` + `soft_helpers.scad` |

Soft helpers: `templates/soft_helpers.scad` (plan fillets, capsules — no BOSL2 required).

## Design defaults (FDM / P1S)

| Concern | Default |
|---------|---------|
| Fit clearance | 0.5–1.0 mm/side (stands ~0.8) |
| Equipment elevated | **open frame, empty under seating**, **TOP-FIRST** |
| Stackable | modular U-sled; posts **outside** chassis XY; annular pads |
| Soft / no-90° | offset footprints, hex/circle voids, 45° language |
| Min feature | ≥ 1.6 mm |
| Overhangs | ≤ 45° |
| Material notes | PETG; PLA fit-check |
| Healthy CGAL Volumes | single solid → **Volumes: 2** (not a failure) |

## DFM laws (non-negotiable)

1. Orientation documented; elevated equipment default **TOP-FIRST** (rim/deck on bed → feet free; state use flip).  
2. Grow structure from print base; no mid-air X-braces.  
3. **Equipment:** empty under seating deck — no waffle/pin forest under bottom-vent gear.  
4. Chassis clearance: posts/tabs outside device XY.  
5. Stack: male + female cup; annular pad recesses (full-cylinder pad cut severs males).  
6. Soft mode: no raw cube language / square lattice as primary look.  
7. Report volume cm³ every redesign.  
8. Critical mating dimensions must be measured, from the user, or fit-tested; assumed precision fits cannot ship.  
9. STL topology must be closed, consistently oriented, and match `expected_components`.  
10. Wet-service parts must be openly drainable, PETG/ASA-class material, cleanable, and mechanically retained.  

Wet fixtures: read `references/wet-service-fixtures.md`.

Deep refs: `references/soft-geometry-dfm.md`, `print-orientation.md`, `understructure-aesthetics.md`, `stackable-open-frame.md`, `intent-lock-and-variants.md`, `iteration-protocol.md`, `print-in-place.md`, `generative-patterns.md`, `regression-test-stand.md`, `hex-platform-studs.md`, **`references/display-enclosure-bezel.md`** (TFT/PyPortal desk shells; bezel face-on-bed + plug +Z; soft G-thin).

### Hybrid + display shells (locked with printables pack)

- **Dimensional bases, bezels, ports, bosses** → this skill (OpenSCAD).
- **Hex/Voronoi lids** → Blender joined-cutter *or* OpenSCAD Voronoi — not pure-Blender ported bases.
- Full Pi case gold: `~/Documents/the-grid/rpi-zero-print-noloop` (SCAD base + Blender hex lid).
- Display desk case gold: `~/Documents/the-grid/pyportal-desk-case` (two-piece soft enclosure).
- Honeycomb Pi case: `enable_keyring=true|false` in SCAD (`false` for noloop packs).

## Export / validate

```bash
# from skill scripts dir (or pack install path)
scripts/export_stl.sh <src_basename>          # needs project-local copy or adapt paths
scripts/validate_export.sh <PROJECT> <ver>    # re-export + gates + dfm_gate.py
scripts/new_part.sh my-bracket bracket
python3 scripts/dfm_gate.py --project DIR --stl DIR/stl/x.stl --mode-file DIR/docs/DESIGN.md
# Optional explicit contract: --expected-components N
```

Docker image: `openscad/openscad:2021.01`, `--export-format=binstl`.

## Previews

Solid multi-view + **under** + cutaway when understructure or to prove empty open frame.  
Ghost chassis ~150×150×50.5 for equipment. Dual-stack still if stack claimed.  
Matplotlib: `linewidths=0`. numpy2: `max-min`, not `.ptp()`.

## Iteration (summary)

Form lock → change budget 1–3 → every version run gates + volume Δ → if worse, revert form.  
Form-reject → new form lock (not endless pin tweaks). Explore ≤5 then **force pick**.

## Project layout

```
~/Documents/the-grid/<part>/
  docs/DESIGN.md
  src/<part>.scad
  stl/<part>.stl
  renders/
  scripts/
  README.md
```

## Common pitfalls

1. CAD before DESIGN.md intent  
2. Pin forest / waffle under equipment seating  
3. Feet-down when TOP-FIRST intended  
4. Posts inside chassis XY  
5. Shipping without `validate_export` / `dfm_gate`  
6. Treating a readable STL or OpenSCAD render as proof of a watertight one-component mesh  
7. Shipping an assumed precision fit without a fit coupon or measurement  
8. Wet-service cups, hidden water traps, or retention based only on friction  
9. Raw STL on Discord (zip)  
10. Polishing five explore variants  
11. Breaking stand v10 regression  
12. **Display bezel plug under bed (−Z)** — face on bed; seating rim must extrude **+Z** (see `references/display-enclosure-bezel.md`)  
13. Soft rounded STLs trip default G-thin HARD on chord length — `soft_mode: yes` and/or `dfm_gate --thin-fail-frac 0.35`; still verify min wall ≥ 1.6 mm in stills  
14. Starting a **ported display base** in Blender — OpenSCAD owns shells; hybrid lids only when lattice is required  
15. Forgetting honeycomb `enable_keyring=false` when Marc wants no keychain loop  

## Verification checklist

- [ ] DESIGN.md intent complete (part-brief)  
- [ ] Class scaffold used  
- [ ] Orientation + use flip in SCAD comments + docs  
- [ ] Docker STL; welded-edge topology and DFM gates PASS  
- [ ] Component count matches `expected_components`  
- [ ] Critical fits are measured/from-user/fit-tested, or design is intentionally non-precision  
- [ ] Wet parts pass drainage, retention, cleanability, and material review  
- [ ] Under preview proves empty open frame when claimed  
- [ ] Print notes + zip  
- [ ] Stand regression green if skill/templates changed  

## Done when

Parametric source + closed gated STL + volume + fit evidence + honest print notes; Marc can send to P1S.  
**HARD DFM fail = not done.**
