# Status — what works, what does not

Written for people who might install this pack, not as a victory lap. Last reviewed 2026-08-24.

## Works well

**Intent-before-CAD.** `printables-part-brief` writing `docs/DESIGN.md` is the highest-leverage piece. Most bad STLs we shipped started as “just sketch it in SCAD.” Product class + orientation + never-list kills pin-forests and feet-down/TOP-FIRST thrash.

**OpenSCAD 2021.01 in Docker.** `openscad/openscad:2021.01` + `--export-format=binstl` is boring and reliable. Host OpenSCAD versions drift; the container does not. Healthy single solids often report `Volumes: 2` in that build — that is not a failure.

**Class scaffolds.** `open_frame_equipment_scaffold.scad`, `soft_part_scaffold.scad`, `part_scaffold.scad`, `pip_hinge_cones.scad` are better starting points than a cube. Soft helpers do fillets/capsules without BOSL2.

**Fail-closed `dfm_gate.py`.** Catches missing DESIGN keys, P1S bed overflow, coarse overhang mass, and **open-under fill** on `equipment-open-frame` (waffle/pins under a seating deck). Topology / welded-edge checks catch garbage meshes. We will not claim “done” on HARD fail.

**Hybrid policy.** Dimensional bases (ports, bosses, pitches) in OpenSCAD. Hex/Voronoi lids in Blender (`pblend`) *or* OpenSCAD Voronoi. Pure-Blender ported bases were a time sink.

**Buy vs print.** `print-vs-buy-shop-fixtures` is a policy skill and it is correct: print L-clips, buy the half-sheet and the rack. Printed cages lose on grams, time, and stiffness.

**Image silhouettes.** Overlay-before-extrude is the whole point. Primitive-CAD mermaids fail icon literacy; a binarized silhouette plus a plate envelope does not.

**Display bezels.** Once you lock “face on bed, stop ring **+Z** only,” PyPortal-class shells stop growing a plug under the bed.

## Works, with sharp edges

**`pblend` / Blender path.** CLI (`doctor`, `new`, `run`, `gate`, `preview`, `pack`) is real. Voxel remesh + solidify-fatten on a ported shell still produces melt. Assembly-only stills hide broken lids. Gate PASS with yikes stills is **not done**.

**G-thin on soft / OCC meshes.** Chord length is not wall thickness. Rounded parts and FreeCAD `exportStl` routinely trip default G-thin HARD. Use `--thin-fail-frac 0.35` **and** still verify ≥ 1.6 mm walls in CAD or slicer. Do not disable the gate.

**Photo metrology.** The image protocol exists. Agents still invent ±0.1 mm fits from one phone pic. The skill is only as good as the human who refuses those numbers.

**`validate_export.sh`.** Useful, but defaults and gold bands are still biased toward one private stand fixture (`dgx-spark-stand` v9/v10) that is **not** in this repo. For generic parts, pass the project path and a basename; do not expect the stand volume band.

**Display enclosure skill.** Laws are good. The gold two-piece case lives in a private tree. Public pack has the procedure and keepout table, not the board-specific STL.

## Does not work well (yet)

**Pack vs live skill drift.** The original house pack lagged the Hermes profile. A `--delete` rsync once wiped a good `dfm_gate.py`. Public `install.sh` is additive on purpose. If you fork this, treat **this git repo** as source of truth and merge profile hotfixes back.

**VibeCAD path is alpha.** `vibecad-printables` documents a real remake loop, but:

- Official Linux build is x86_64. aarch64 needs qemu + a sysroot dance.
- Host Python has no `FreeCAD` module — scripts must run inside VibeCAD/`freecadcmd`.
- Enabling MCP disables the in-app assistant.
- `multiFuse` does not weld like OpenSCAD `hull()`. Coupon remakes can stay multi-solid.
- Do not ship from a `.FCStd` preview.

**G-open-under can be gamed.** Reclassifying equipment as `tray` silences the open-under HARD check. That is a metadata cheat, not a design fix. The gate cannot stop a dishonest `product_class`.

**No slicer estimates.** Support volume, time, and filament are not gated. Print notes are still human.

**No published gold STLs.** Regression fixtures (DGX stand, Pi Zero hybrid pack, PyPortal shell) stay private because they mix shop photos, hub URLs, and household inventory. Public CI only runs synthetic mesh + CLI unit tests.

**Blender MCP “rocket demos.”** Viewport-pretty organic toys are a different quality bar. We do not treat them as FDM craft.

**CadQuery / live MCP / slicer CLI.** Called out as phase 2 in the old pack README. Still not here.

**House-only tools we did not publish**

| Thing | Why it stayed private |
|-------|------------------------|
| `~/Documents/the-grid/*` parts | Household / lab geometry, kids kits, shop photos |
| `cad-step-part-extract` | Tied to a specific vendor assembly and house CNC recipe |
| `measure-desk` | Phone-scan / household metrology, not a portable FDM tool |
| Hub 3D viewers, filament queue | Private surfaces and inventory |

## Recurring footguns (if you only read one list)

1. CAD before DESIGN.md
2. Pin forest / waffle under bottom-vent gear
3. Feet-down when the brief said TOP-FIRST
4. Bezel seating plug at −Z
5. Nested `offset()` soap-dish floors on display trays
6. Shipping after Docker export without `dfm_gate.py`
7. Treating OpenSCAD `Volumes` as topology proof
8. Raw `.stl` on chat apps (zip it)
9. Polishing five explore silhouettes instead of picking one
10. `import bpy` on host Python

## Compatibility we actually run

- Bambu Lab P1S (256 mm bed) — defaults in the gate
- OpenSCAD Docker tag `2021.01`
- Blender 4.x headless for lids
- Hermes Agent skill loader + `/printables` bundle

Other printers: change `--p1s-bed` / DESIGN bed notes. Other agents: the Python/bash tools do not require Hermes.
