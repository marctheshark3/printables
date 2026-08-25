---
name: printables-display-enclosures
description: "Use for PyPortal/TFT desk cases. OpenSCAD two-piece + ports."
version: 1.0.0
author: Tron
license: MIT
metadata:
  hermes:
    tags: [3d-print, enclosure, display, pyportal, openscad, dfm, printables, bambu]
    related_skills: [openscad-printables, printables-part-brief, printables-dfm-gate, blender-printables]
    gold: "~/Documents/the-grid/pyportal-desk-case"
---

# Printables display enclosures

Class skill for **board + screen** cases (lab COP, desk shell). CAD backend default = **OpenSCAD**. Lattice lids only via hybrid/Blender policy.

## When to use

- PyPortal / TFT / touch panel desk case
- Bare mainboard display enclosure
- Port cutouts (USB, microSD, STEMMA) + bezel window
- After Marc rejects ugly trays (“yikes”, “seems bad”)

**Don’t:** pure-Blender ported display bases; themed Adafruit floppy/LCARS unless brief is themed; ship on DFM PASS alone.

## Hard sequence

1. **part-brief** → DESIGN.md (`product_class: enclosure`, soft_mode, fit tags)
2. **vision_analyze** board **front + back** → I/O edge map
3. Dims table: PCB outer from datasheet; I/O from connector standards or calipers
4. OpenSCAD two-piece: **base** + **bezel** (separate STLs)
5. Docker export each → `dfm_gate` each (`--thin-fail-frac 0.35` if soft rounded)
6. Separate stills → vision — **yikes = rewrite form, not tweak knobs**
7. Zip for Discord

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

## Connector keepouts (defaults)

| Port | Window W×H mm | Basis |
|------|---------------|--------|
| micro-USB Type-B | **13.0 × 8.5** | Plug ~10.6×8.5 + slack |
| microSD | **16.0 × 3.5** | Card + path |
| STEMMA QT pair | **22 × 9** | JST-SH pair |
| STEMMA single | **10 × 8** | one JST-SH |
| RESET poke | Ø6.5–7 | face |

See also openscad-printables `references/connector-keepouts-fdm.md` when present.

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

`~/Documents/the-grid/pyportal-desk-case` v0.3.x clean rewrite.

## Pitfalls

1. Wrong edge from skipping back-photo vision  
2. USB hole too tight for overmold  
3. Bezel plug at −Z  
4. Polishing soap-dish instead of rewrite  
5. Assembly-only preview  
6. Inventing M2.5 pitch as fact  

## Done when

Gated base+bezel + honest stills + zip + DESIGN keepout table.
