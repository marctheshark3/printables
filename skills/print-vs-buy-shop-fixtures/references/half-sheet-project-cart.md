# Half-sheet project cart (hybrid) — locked 2026-08-20

Marc override: $80 aluminum half-height cart rejected as too expensive. Print a functional bakery-rack copy **sized for 3 live projects**, not a 10-tier PETG sculpture.

## Architecture

- Four 1×2 S4S poplar posts + 8 stretchers (top/bottom, width/depth).
- 12 printed PETG **C-rails** (180 mm), two per side per tray, through-screwed into the inner post face.
- Rolled rim trapped in ~8 mm channel (lower ledge + 45° upper lip). Front open; rear bumper.
- 8 printed corner gussets, 4 caster shoes, 1 spacing jig.
- Fourth 13×18 pan is the top deck (screw it down).
- Envelope ~14.6 × 19.5 × 24.4 in with 2 in casters.
- Prototype load: 10 lb/tray, 35 lb total. Not a certified rating.

## Wood

- Home Depot Builders Choice **1×2×8 S4S poplar 4-pack**: https://www.homedepot.com/p/Builders-Choice-1-in-x-2-in-x-8-ft-S4S-Poplar-Board-4-Pack-HLPO1028XX/205949289
- Single: https://www.homedepot.com/p/Builders-Choice-1-in-x-2-in-x-8-ft-S4S-Poplar-Board-HLPO10208X/206201562
- Actual ~0.75 × 1.5 in (19 × 38 mm). Cut list ~18 ft → 3 boards min, 4-pack is the buy.
- Width stretchers **set from the actual pan**, not CAD.

## Source of truth

`~/Documents/the-grid/husky-sheet-pan-rack/`

- `docs/DESIGN.md`, `src/half_sheet_project_cart.scad`
- STLs: `pan_slide_clip` (C-rail), `corner_gusset`, `caster_shoe`, `spacing_jig`
- Joint explainers: `renders/joint_rail_section.png` (money shot), `joint_slide_clip.png`

## Pitfalls

- P1S cannot print 13–18 in rails as one stick. Segment or use lumber for span.
- Old gravity L-clip assembly looked like floating trays — do not regress.
- Caster hole pattern still assumed until owned casters are measured; print one shoe first.
- Aluminum is conductive: mat/standoffs; no loose LiPo on the pan.
