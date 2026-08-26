# CAD/CAM contract v1

`docs/PRINT_SPEC.yaml` is the only machine-readable source of truth. CAD backends consume it. Mesh validation proves exported bodies. Narrative Markdown may explain decisions but is never parsed.

An assembly is multiple independently manufactured bodies: one `geometry.stl_files[]` entry each. Bodies may mate after manufacture; they must not occupy the same exported solid.

## Required invariants

- millimetres, Z-up
- parametric source: `cad.parametric: true`
- overlapping exported solids forbidden (`geometry.overlapping_solids_allowed: false` and mesh occupancy checks)
- one STL per independently manufactured body
- every STL declares its expected closed shell count
- every critical dimension declares value, tolerance, provenance, and a CAD parameter
- fit clearance is **per side**
- assumed critical fits cannot ship
- every STL must be closed, consistently oriented, manifold, and non-self-intersecting

## Backend selection

| Need | `cad.backend` |
|---|---|
| dimensional mechanical part, exact fits, brackets, stands, enclosures | `openscad` |
| organic skin, lattice, sculpted surface | `blender` |
| separate declared dimensional and organic bodies | `hybrid` |

If more than one row seems plausible, choose `openscad`.

## Tolerance vocabulary

- `clearance_per_side_mm`: gap on each mating side
- `tolerance_mm`: allowed dimensional error around a nominal value
- `source`: `measured`, `from-user`, `datasheet`, `fit-tested`, or `assumed`
- `fit.required: true` requires `measured`, `from-user`, `datasheet`, or `fit-tested` evidence and a named fit coupon unless evidence is `fit-tested`
- `fit.coupon` is a project-relative path when it names a file; that file must exist
- `service.drainage`: dry may use `none`, `not-applicable`, or `unspecified`; wet requires `open-continuous`, `through-drain`, `drainable`, or `slots`

Fit, drainage, and material policy are enforced only by the spec validator. The mesh tool does not re-encode those rules.

## Proof boundary

The contract describes intent. It does not prove geometry. After export, `validate_project.py` independently verifies:

1. spec is complete and files exist
2. each CAD parameter is declared in source
3. each STL parses, is watertight, and has positive signed volume
4. shell count matches the spec
5. exported shells do not occupy the same space
6. bounding box fits strictly inside the machine envelope
7. overhang and class-specific DFM heuristics

A preview is not proof. An STL that opens is not proof. `HARD=0` is necessary; visual inspection and fit evidence are still required.
