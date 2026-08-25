---
name: blender-printables
description: "Use when organic/lattice/boolean FDM parts need headless Blender bpy → STL after intent lock. CLI pblend; light cleanup default; DFM + vision; OpenSCAD stays dimensional default."
version: 0.2.1
author: Marc Mailloux (marctheshark), Hermes Agent / Tron
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [blender, bpy, 3d-print, stl, bambu, p1s, printables, voronoi, dfm]
    related_skills: [printables-part-brief, printables-dfm-gate, openscad-printables]
    regression_fixture: "~/Documents/the-grid/rpi-zero-voronoi-noloop"
---

# Blender Printables v0.2 — FDM craft, not demo rockets

## Overview

Headless **Blender 4.x** (`bpy`) → STL for **Bambu P1S**, then **dfm_gate** + **look check**.

This is **not** the online “MCP makes a rocket” path. Demos optimize viewport beauty. We optimize **printable mechanical parts** (with optional organic lids).

Loop:

1. `printables-part-brief` → DESIGN.md (`scaffold: blender-bpy` when Blender is right)
2. **This skill** + **`pblend` CLI**
3. `printables-dfm-gate` + separate stills (vision)

OpenSCAD remains **dimensional default**. Optional live explore: hermes `blender-mcp` (GUI/Xvfb) — still export via `pblend` for ship.

**Gold print pack (hybrid):** `~/Documents/the-grid/rpi-zero-print-noloop`  
OpenSCAD base (no keyring) + Blender hex lid. See `references/fdm-craft.md`.

**Blender lid SoT:** `~/Documents/the-grid/rpi-zero-voronoi-noloop` (hex plate, joined cutter).  
**OpenSCAD case SoT:** `~/Documents/the-grid/rpi-zero-honeycomb-case` (`enable_keyring`).

## When to Use

- Hex / honeycomb / Voronoi **lids** (joined-cutter plate)
- Organic skin half of a **hybrid** case
- Marc asks Blender after part-brief chose hybrid/organic

**Don’t:** pure-Blender ported bases as default; capsule-soup Voronoi; voxel+fatten shells; skip vision; ship without gate; `import bpy` on host Python.

## Hybrid orchestration (preferred for enclosures)

1. part-brief → DESIGN.md notes `backend: hybrid` or base=openscad / lid=blender-bpy  
2. OpenSCAD export base (ports, bosses)  
3. `pblend run --which lid` for lattice half  
4. Collect STLs into one project folder → separate stills → gate each → one zip  
5. Example: `rpi-zero-print-noloop`

## Prerequisites

```bash
PBLEND=~/.hermes/profiles/tron/skills/creative/blender-printables/scripts/pblend
# pack SoT: ~/Documents/the-grid/printables-skill-pack/skills/blender-printables/scripts/pblend
terminal: "$PBLEND" doctor
```

Blender ≥4.0, numpy (bundled), scipy if Voronoi, `dfm_gate.py` resolvable.

## How to Run

```bash
PBLEND="$HOME/.hermes/profiles/tron/skills/creative/blender-printables/scripts/pblend"
"$PBLEND" doctor
"$PBLEND" new my-part --class enclosure
# edit src/build.py — cleanup_fdm(obj, mode="light") on shells
"$PBLEND" run --project "$HOME/Documents/the-grid/my-part"
"$PBLEND" gate --project "$HOME/Documents/the-grid/my-part"
"$PBLEND" preview --project "$HOME/Documents/the-grid/my-part"   # then vision_analyze each half
"$PBLEND" pack --project "$HOME/Documents/the-grid/my-part" --version v0.1.0
```

## Hard sequence

```
0. DESIGN.md locked (class, orientation, scaffold: blender-bpy)
1. Backend check: if dimensional-only → hand off openscad-printables
2. Build parametric bpy (mm, Z-up)
3. cleanup_fdm mode=light on shells; voxel only on lattice soup if required
4. pblend run → separate STLs per printable body
5. pblend preview → base-* and lid-* stills (not assembly-only)
6. vision_analyze stills — fix geometry if yikes (do not ship melt)
7. pblend gate HARD=0
8. pack zip for Discord
```

## FDM craft (read)

- `references/fdm-craft.md` — cleanup modes, boolean order, routing
- `references/skill-gap.md` — why rockets ≠ Pi cases
- `references/when-blender-vs-openscad.md`
- `references/headless-gotchas.md`
- `references/gold-rpi-zero-voronoi.md`

```python
import os, sys
sys.path.insert(0, os.environ["PBLEND_LIB"])
from bpy_lib.fdm_cleanup import cleanup_fdm
cleanup_fdm(shell, mode="light")   # DEFAULT
# cleanup_fdm(lattice, mode="voxel", voxel=0.32)  # lattice only
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `pblend doctor` | Blender + deps + dfm_gate |
| `pblend new <name>` | Scaffold the-grid project |
| `pblend run --project DIR` | `blender -b -P` build |
| `pblend gate --project DIR` | dfm each printable STL |
| `pblend preview --project DIR` | Workbench stills |
| `pblend pack --project DIR` | Zip deliverable |

## Optional MCP explore

Hermes catalog skill `blender-mcp`: live `execute_blender_code` + viewport screenshots.  
Use to **iterate look**, then bake into a `src/build_*.py` and ship with `pblend`.  
Requires Blender GUI or `xvfb-run blender` + addon connect. Not required for batch gold.

## Pitfalls

1. Voxel remesh / solidify fatten on ported shells (melt)  
2. Shipping combined assembly preview only  
3. Gate PASS without eyes on stills  
4. CAD before DESIGN.md  
5. Host `import bpy`  
6. Photo-guessed port X  
7. Using Blender for equipment-open-frame stands  
8. Treating MCP rocket demos as FDM quality bar  
9. Raw STL on Discord  
10. Breaking noloop / lattice gold without re-gate + re-look  

## Verification

- [ ] Backend choice documented  
- [ ] Shells used `cleanup_fdm(mode="light")`  
- [ ] Separate stills look intentional (vision or Marc)  
- [ ] Gate HARD=0  
- [ ] Bbox ≤ 256³  
- [ ] Zip pack  
- [ ] Gold noloop still green after shared helper changes  

## Done when

Parametric bpy + clean stills + gated STLs + zip. **Yikes stills = not done** even if gate passes.
