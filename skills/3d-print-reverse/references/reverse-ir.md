# Reverse IR (`reverse/<body>.ir.json`)

`docs/PRINT_SPEC.yaml` stays the manufacturing contract. The IR is the only rebuild input. Markdown cannot override it.

- `schema_version: 1`
- `units: mm`
- Arrays sorted by stable id
- Floats fixed to 6 decimal places
- Always store `raw_mm` and `value_mm`
- Mesh-derived dimensions are `source: measured`
- Do not snap to “nice” numbers unless `--snap-mm` is set
- Every IR dimension becomes a PRINT_SPEC `dimensions[]` row with the same `parameter`

v1 features: sketch on `xy|xz|yz|offset|midplane|3-point`; extrude add/cut (blind, through-all, to-face); revolve; loft; boolean union/subtract; hole; fillet; chamfer; mirror; pattern when evidenced. No T-splines in v1.

`forbidden.triangle_wrapped_step` is always true: if STEP face count ≥ 0.9 × input triangles, refuse to write `step/` and exit non-zero.
