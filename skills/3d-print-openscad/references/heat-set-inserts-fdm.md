# Heat-set brass inserts for FDM

Default fastening for printed parts is a **heat-set brass insert**, not a
printed thread. Printed ISO metric coarse thread is an explicit opt-in
(`templates/printed_thread.scad`).

Tag `dimensions[].source` as `datasheet` or `measured`. `assumed` insert OD
is HARD when `fit.required: true`.

## Provenance

Hole diameters and insert lengths follow the public CNC Kitchen / ruthex
FDM application note for tapered helical brass inserts (M2 / M3 / M4).
Major OD is the knurl envelope from the same datasheet class, not a guess.
Verify the vendor drawing for the exact SKU before a fit-critical ship.

| Size | Insert major OD mm | FDM hole Ø mm | Insert length mm | Min boss OD mm (OD + 2×1.6 wall) |
|------|--------------------|---------------|------------------|----------------------------------|
| M2 | 3.5 | 3.1 | 4.0 | 6.7 |
| M3 | 4.6 | 4.0 | 5.7 | 7.8 |
| M4 | 6.3 | 5.6 | 8.1 | 9.5 |

Use `templates/insert_boss.scad` and `templates/insert_coupon.scad`. Map
`insert_od_mm`, `insert_hole_d_mm`, `insert_depth_mm`, and `boss_od_mm` in
`PRINT_SPEC.yaml`.
