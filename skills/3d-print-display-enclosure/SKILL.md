---
name: 3d-print-display-enclosure
description: Build two-piece FDM enclosures for small displays.
version: 1.0.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [3d-print, enclosure, display, openscad, dfm]
    related_skills: [3d-print-openscad, 3d-print-design-brief, 3d-print-validate, 3d-print-blender, 3d-print-pack]
---

# 3D Print Display Enclosure

Class skill for **board + screen** cases (lab COP, desk shell). CAD backend default = **OpenSCAD**. Lattice lids only via hybrid/Blender policy.

## When to use

- PyPortal / TFT / touch panel desk case
- Bare mainboard display enclosure
- Port cutouts (USB, microSD, STEMMA) + bezel window
- after visual review rejects the current tray form

**Don’t:** pure-Blender ported display bases; themed Adafruit floppy/LCARS unless brief is themed; ship on DFM PASS alone.

## Hard sequence

1. **3d-print-design-brief** → `docs/PRINT_SPEC.yaml` (`product_class: enclosure`) with one STL entry each for **base** and **bezel**
2. **vision_analyze** board **front + back** → I/O edge map
3. Dims table: PCB outer from datasheet; I/O from connector standards or calipers
4. OpenSCAD two-piece: **base** + **bezel** (separate STLs)
5. Docker export each → `3d-print-validate/scripts/validate_project.py`
6. Separate stills → vision — **yikes = rewrite form, not tweak knobs**
7. Package the deliverables with `3d-print-pack`

## Geometry laws (session-hard)

| Law | Detail |
|-----|--------|
| Flat floor | One cavity extrude from `floor_t`. Nested `offset()` → **soap-dish pyramid** (rejected) |
| Posts | Corner cylinders + through-holes; tag mount pitch |
| Bezel orient | Face on bed (`z=0`); stop ring **+Z** only |
| Bezel shape | Face + stop ring + window + button. **No** side cube gouges |
| I/O on base walls | Rectangular keepouts at correct z0 |
| Tilt | Off by default; separate stand if needed |
| Hybrid | OpenSCAD owns shell; Blender only organic/hex lid half |

## Connector keepouts

Use `3d-print-openscad/references/connector-keepouts-fdm.md` as the only table
for USB, microSD, STEMMA, and RESET windows. Do not copy those numbers here.

### PyPortal placement (owned board photo)

- USB + microSD → **one short edge** (not long)
- STEMMA → **opposite short edge**
- PCB outer: **88.3 × 64.3 × 11** (Adafruit 4116)
- Mount pitch: measure; 3.5 mm inset estimate → tag **assumed**

## Quality bar

- DFM **PASS ≠ done**. Reject melt, soap-dish, torn frames on stills.
- Product tray + picture-frame, not a sink.
- Themed X posts are a **different brief**.

## Gold

A validated two-piece display-enclosure fixture should remain in downstream regression suites.

## Pitfalls

1. Wrong edge from skipping back-photo vision  
2. USB hole too tight for overmold  
3. Bezel plug at −Z  
4. Polishing soap-dish instead of rewrite  
5. Assembly-only preview  
6. Inventing M2.5 pitch as fact  

## Done when

Gated base+bezel + honest stills + `3d-print-pack` zip + PRINT_SPEC keepout table.
