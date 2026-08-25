# Generative / load-path design (parametric, printable)

Goal: parts that look **organic / cool**, use less material, and still **print** on FDM — without requiring Fusion Generative Design.

There are three tiers. Prefer the lowest tier that meets the brief.

## Hard guardrail (from stand v6–v9)

**Do not use pin/branch stilts under equipment seating decks** as “generative.”  
Stand v6 load-path pins were volume-OK and FDM-OK — Marc still rejected them as “little cylinders.”  
For DGX-class elevated bases: **open frame + perimeter load paths** (pillars, edge beam, windowed skirt). Generative T0 applies to **structure language that remains readable**, not density of pins.

| Product | Generative OK | Generative NOT OK |
|---------|---------------|-------------------|
| Open-frame equipment base | Variable pillar/edge thickness, organic window cutouts, hex deck voids | Pin forest, waffle fill under device |
| Soft tray needing midspan | Soft waffle pitch map, load-path ribs | Random unique stilts as visual primary |
| Bridge / bracket | Truss chords, branch members | Unsupported mid-air members |

## Tier 0 — Parametric “organic by construction” (default)

Stay in OpenSCAD. Encode load paths as geometry rules:

| Pattern | Idea | Print notes |
|---------|------|-------------|
| **Perimeter load paths** | Thick at corners/pillars → thin mid-span open | **Default for equipment** (stand v9) |
| **Load-path ribs** | Thick along force lines; thin elsewhere | Ribs ≥ 1.6 mm; readable walls not pins |
| **Branch / tree members** | Thicker at base, taper; merge into nodes | Bridges/brackets only — **not** under DGX seating |
| **Hex / Voronoi-ish decks** | Parametric hex grid or jittered circular voids | Bars ≥ 2.0–2.4 mm; seating surface only |
| **Gyroid / TPMS shell** (approx) | Layered sinusoidal walls | Prefer **slicer gyroid infill** for bulk |
| **Truss from nodes** | Node graph + hull members | Bed-reachable or ≤45°; not pin forest |
| **Variable density zones** | Dense near mounts; sparse mid-span | Pitch/width params — not voxel TO |

These give the **look and intent** of generative design while remaining editable and manifold.

Templates: `templates/soft_helpers.scad`, `templates/open_frame_equipment_scaffold.scad`, `templates/generative_loadpath.scad`.

## Tier 1 — Constraint-driven parameter search

Keep SCAD parametric; search parameters under constraints:

- volume ≤ V_max
- outer bbox ≤ printer
- min feature ≥ 1.6 mm
- max free bridge ≤ 12 mm
- stilts unique-grid → Simple:yes

Workflow:

1. Expose knobs (`stilt_pitch`, `rib_w`, `hex_r`, `buttress_w`, `wall`).
2. Export a few variants via CLI `-D`.
3. Report volume + bbox table; pick Pareto (stiffness proxy vs plastic).

Stiffness proxy without FEA: shorter free spans, more buttresses, thicker load-path ribs. Be honest that this is **heuristic**, not FEA.

Optional future: small Python loop calling Docker OpenSCAD + numpy-stl volume (no FEA).

## Tier 2 — Topology optimization → clean → re-parameterize

True TO (SIMP etc.) for when Marc wants bridge/bracket-class organic structure.

Open-source path (research-backed, not installed by default):

- **PyTopo3D** (Python SIMP, STL domain in/out) — research/prototype path.
- FreeCAD + CalculiX topology workbench.
- Classic TopOpt 88/99-line family for education.

**Critical rule for this skill:** do **not** print raw TO mesh as the final product if we can avoid it.

Pipeline:

1. Define design domain, non-design (bolts, contact pads), loads, volume fraction.
2. Run TO → density field / mesh.
3. **Clean**: manifold repair, thickness thresholds, overhang filter for FDM.
4. **Re-express** as parametric SCAD (or build123d) load-path approximation when possible — so Marc can still edit.
5. If mesh must ship: validate manifold, add print orientation notes, expect supports more often.

Raw TO meshes often:

- have thin features < nozzle
- need heavy supports
- are non-parametric (iteration pain — the failure mode Marc already hit)

## Bridge example (how to think)

Bad: solid rectangular bar.

Better parametric generative:

1. Span L, depth D, load midspan or distributed.
2. Keep top chord (compression) + bottom chord (tension) + diagonal members ≤45° or verticals from bed if print upright.
3. Hollow/fillet joints; soft outer silhouette.
4. Remove material outside stress envelope via hex voids / taper.
5. Report volume vs solid bar %.

## When NOT to go organic

- Tight envelope with many port cutouts (stands, enclosures) — soft open-frame + perimeter structure wins.
- First fit-check prototypes — simple parametric first.
- Marc said “minimal plastic” and form is already liked — don’t reinvent silhouette.
- “Make underside cooler” on equipment bases — do not invent pin forests; open empty is the cool product answer.

## Honesty bar

Always label:

- **Heuristic generative** (Tier 0/1) vs **FEA/TO-backed** (Tier 2).
- Volume (cm³) and % of solid bounding body.
- Supports expectation after DFM pass.
