# Printable Part Contract v1

`docs/PRINT_SPEC.yaml` is the machine-readable source of truth for every FDM project. CAD backends consume it; STL validation enforces it. Narrative Markdown may explain decisions but must not override this file.

## Required invariants

- millimetres, Z-up
- parametric source: `cad.parametric: true`
- no overlapping printable solids: `geometry.overlapping_solids_allowed: false`
- one STL per independently printed body
- every STL declares its expected closed shell count
- every critical dimension declares value, tolerance, and provenance
- fit clearance is **per side**, never ambiguous total clearance
- assumed critical fits cannot ship
- every STL must be closed, consistently oriented, manifold, and non-self-intersecting

## Backend selection

| Need | `cad.backend` |
|---|---|
| dimensional mechanical part, exact fits, brackets, stands, enclosures | `openscad` |
| organic skin, lattice, sculpted surface | `blender` |
| separate declared dimensional and organic bodies | `hybrid` |

If more than one row seems plausible, choose `openscad`. Do not choose a backend because it is novel.

## Tolerance vocabulary

- `clearance_per_side_mm`: gap on each mating side
- `tolerance_mm`: allowed dimensional error around a nominal value
- `source`: `measured`, `from-user`, `datasheet`, `fit-tested`, or `assumed`
- `fit.required: true` requires `measured`, `from-user`, `datasheet`, or `fit-tested` evidence and a named fit coupon unless evidence is `fit-tested`
- `fit.coupon` is a project-relative path when it names a file; that file must exist
- `service.drainage`: dry may use `none`, `not-applicable`, or `unspecified`; wet requires `open-continuous`, `through-drain`, `drainable`, or `slots`

## Proof boundary

The contract describes intent. It does not prove geometry. The validator must independently verify:

1. file exists and parses
2. triangle count is sane
3. closed manifold topology
4. consistent face orientation
5. shell count equals the spec
6. no duplicate or degenerate faces
7. bounding box fits the printer
8. positive volume
9. overhang policy
10. backend-specific solid validity before STL export

A preview is not proof. An STL that opens is not proof. `HARD=0` is necessary; visual inspection and fit evidence are still required.
