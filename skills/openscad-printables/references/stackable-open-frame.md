# Stackable equipment frames (DGX-class desk stacks)

Project: `~/Documents/the-grid/dgx-spark-stack/`  
Chassis: NVIDIA DGX Spark **150 × 150 × 50.5 mm**, bottom vents, rear I/O.

## When

Marc wants stack / tower / “stack on top” + airflow + sleek minimal for bottom-vent gear.

## Community inspiration (research before greenfield stack CAD)

When form is rejected or stack is new, **look at real desk stacks first** (Printables / Thingiverse / NVIDIA forum), then lock form:

| Source | Takeaway |
|--------|----------|
| **SchwickSchwimmer** On Desk Stack Stand | Continuous soft **U-shell / sled** furniture language; open airflow; portable; dual hold |
| **DLVR8R** dual stand | Low retention walls; **~9.5–10 mm** inter-chassis gap; snug rails; PETG for heat |
| Open **rack trays** (Paul Aviles / commercial) | Empty floor under unit for intake — not filled lattice |

Do **not** invent a tall four-post cage as the default “stack” answer. Tower cages read as product-wrong for desk sleeks.

## Preferred product: modular **U-sled** (v2 active)

```
identical modules (print N)
  soft three-sided U-rail (open rear I/O)
  open floor — seating edge beam + corner fuse only; EMPTY midspan
  under clearance_z empty (bottom intake; v2 uses ~22 mm for sleeker desk)
  short corner STACK TABS outside chassis XY
  tabs rise to seating + spark_h + inter_gap (~10 mm)
  tab tops: female cups
  tab feet: male tapers + annular pad recesses
Print: TOP-FIRST (tab tops on bed → males free)
Use: flip; next sled feet land on lower tab cups
```

### Stack pitch (use)

```
tab_top_z = clearance_z + spark_h + inter_gap
// v2: 22 + 50.5 + 10 = 82.5 mm between sled foot planes
```

### Chassis clearance (hard fail)

Tabs/posts must not intersect device solid:

```
tab_pitch = spark_xy + tab_w + 2 * tab_gap   // gap ≥ ~2.5–3 mm
tab_inner_face = tab_pitch/2 - tab_w/2
// require: tab_inner_face >= spark_xy/2 + tab_gap
```

Echo `tab_inner_face` and `spark_half` in SCAD.  
Fuse U-rail to tabs with **corner lobes** — tabs outside pocket ring will float disconnected if you only extrude the pocket ring.

## Archive pattern: four-post open cube (v1)

Rejected for desk stack (“this ain’t it”): tall posts, large XY, cage silhouette, high plastic (~347 cm³).

Still valid DFM lessons: outside-chassis pitch, annular pads, Volumes diagnostic, empty midspan.  
Files: `src/dgx_spark_stack_v1.scad` · bbox ~222² × 113.5 · ~347.5 cm³.

## Male / cup / pad fusion

| Feature | Rule |
|---------|------|
| Male | frustum; `pin_fuse` ≥ ~1.0–1.2 mm volume overlap into foot/tab |
| Cup | open at bed face in TOP-FIRST; mouth chamfer; radial clear ~0.35–0.45 mm |
| Pad recess | **annular** if co-axial with male: `difference(){ cyl(pad_d); cyl(pin_d0+margin); }` with `pad_d > pin keep-out` |
| Fail mode | full `cylinder(d=pad_d)` through foot slab **deletes male root** → floating pins |

## OpenSCAD Volumes diagnostic (2021.01 Docker)

| Result | Meaning |
|--------|---------|
| Volumes **2** | Healthy single solid (exterior + material) |
| Volumes **3** | Closed cavity **or** two separate solids (+ exterior) |
| Volumes **1+N** | N separate solids (e.g. body + 4 severed males → **6**) |

Probe with toggles: males / cups / pads independently.  
`Simple: yes` alone is not enough — always read Volumes.

## Plastic

- Tall full-height posts dominate cm³ → prefer **short tabs** + thin U-rail (v2 ~147 cm³).
- Prefer thin seating ring + corner lobes over full outer plate to post envelope.
- Report cm³ every redesign + Δ vs prior form.

## Preview gates

- Under: empty midspan (no waffle/pins)
- Iso/hero: U-rail + tabs **outside** pocket; cups on tab tops
- Optional `show_stack2` assembly for pitch check
- Matplotlib / numpy 2: use `max-min`, not `.ptp()`

## Validation snapshots

| Ver | Form | BBox (mm) | cm³ | Pitch | Verdict |
|-----|------|-----------|-----|-------|---------|
| v1 | four-post cube | ~222² × 113.5 | ~347.5 | ~104.5 | rejected — cage/tower |
| **v2** | **U-sled + short tabs** | **~199² × 85.5** | **~146.8** | **82.5** | **active desk stack** |

STL: `stl/dgx_spark_stack_v2.stl` · SCAD: `src/dgx_spark_stack_v2.scad` · DESIGN: `docs/DESIGN_v2.md`

## Form-reject rule

If Marc says **“this ain’t it” / different version / not the tower**:

1. Stop iterating that silhouette.
2. Research community desk stacks (table above).
3. New form language lock in `DESIGN_vN.md` + change budget.
4. New SCAD version (or greenfield file) — not a param tweak on the hated form.
