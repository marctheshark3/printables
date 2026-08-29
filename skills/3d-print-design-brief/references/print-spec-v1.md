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
| human is already in 10-X-eng/vibecad, or an explicit remake of a PRINT_SPEC part there | `vibecad` |
| reverse-engineered analytic STEP via CadQuery Docker (OCC) | `cadquery` |

If more than one row seems plausible, choose `openscad`. `vibecad` is an optional third backend, not the default for a new bracket, and not the PyPI package named vibecad. `cadquery` is the same bar as `vibecad`: parametric Python source, millimetres, named parameters. `hybrid` still means separate bodies, not two kernels editing one body. VibeCAD chat, `.FCStd`, MJCF, and `DESIGN.md` cannot override this file.

## Optional `pack`, `slice`, and `fit.measured_mm`

Ignored when absent so existing examples stay valid.

- `pack.required`: policy flag for agents that already demand a zip. The zip is produced by `3d-print-pack` after `validate_project.py` HARD=0. The zip file itself is not required for unit CI.
- `slice.process_card` / `slice.three_mf`: project-relative paths. If named, `check_files` requires they exist. A process card is JSON from spec `print:` and `manufacturing:`. A 3MF is emitted only by a local slicer CLI (`ORCA_SLICER` / `BAMBU_STUDIO` / `PRUSA_SLICER`); never an empty or STL-renamed file. No printer IP field.
- `fit.measured_mm`: mapping of CAD parameter → caliper millimetres written by `record_fit.py`. Never invent a measurement.

`geometry.min_wall_mm` is also a mesh gate: sampled inward-ray thickness HARD-fails when more than `thin_wall_area_frac=0.02` of sampled area is below that value (0.05 mm tessellation slack). Split-for-bed repairs envelope HARD with two `geometry.stl_files[]` entries; it does not scale the part.

Assumed insert OD (`insert_od` / `insert_od_mm` and heat-set aliases) is HARD when `fit.required: true`. Use `datasheet` or `measured`. Printed ISO metric thread is opt-in; default is heat-set (`references/heat-set-inserts-fdm.md`).

Live printer control is the sibling `bambu-mcp` repo. This contract never stores printer identity.

## Optional `reverse` block

Ignored when absent so existing examples stay valid. When present it cannot invent CAD: `reverse.class` is `parametric`, `analytic`, `organic`, or `failed`. Reverse projects use `cad.backend: vibecad` or `cadquery` (organic is blender only). `reverse.input_stl` and `reverse.ir` are project-relative. `reverse.step_files` is optional and does not have to exist for unit CI. Markdown cannot override the IR.

## Tolerance vocabulary

- `clearance_per_side_mm`: gap on each mating side
- `tolerance_mm`: allowed dimensional error around a nominal value
- `source`: `measured`, `from-user`, `datasheet`, `fit-tested`, or `assumed`
- `fit.required: true` requires `measured`, `from-user`, `datasheet`, or `fit-tested` evidence and a named fit coupon unless evidence is `fit-tested`
- `fit.coupon` is a project-relative path when it names a file; that file must exist
- `service.drainage`: dry may use `none`, `not-applicable`, or `unspecified`; wet requires `open-continuous`, `through-drain`, `drainable`, or `slots`

Fit, drainage, and material policy are enforced only by the spec validator. The mesh tool does not re-encode those rules.

## Product class `robot-module`

Optional `hardware` and `wiring` blocks are ignored unless present, except `robot-module` which requires non-empty `hardware.components`. Markdown cannot add a BOM.

`hardware.components[]` fields: `id`, `mpn_or_generic`, `role`, `qty`, `envelope_mm` as `[X, Y, Z]` millimetres, and `interfaces[]` using the same `name` / `parameter` / `value_mm` / `tolerance_mm` / `source` rules as `dimensions[]`. Critical MCU, servo, motor, and drive interfaces cannot use `source: assumed`. Motors, batteries, MCUs, servos, bearings, and extrusion frames are bought parts in this block, never printable bodies.

`wiring` when present requires `voltage_domains` (`name`, `volts`), `nets` or `pin_map` (`mcu_pin`, `function`, `voltage`), `connector_keepouts`, and named `cable_path_keepouts`. Keepouts map to CAD parameters (`parameter`, `width_mm`, `height_mm`, `source`). A 3V3/5V collision is one net or pin claimed on both domains, not the mere presence of both rails.

## Optional assembly, loads, and scene

Ignored when absent. When present they cannot be assumed, and Markdown / MJCF / URDF / USD cannot supply them.

`assembly.bodies[]`: unique `id`; exactly one of printed `body` (`geometry.stl_files[].body`) or `hardware` (`hardware.components[].id`); `parent`; `pose.xyz_mm` and `pose.rpy_deg` in `assembly.frame`. Several bodies may instance one STL. Hardware envelopes occupy assembled space and are bought, not printed.

`assembly.joints[]`: `id`, `type` (`fixed` | `revolute` | `prismatic`), `parent`, `child`, `axis`, `clearance_per_side_mm`, `source`. Revolute joints require `limits.min_deg` / `max_deg`. Joint `source` cannot be `assumed`.

`loads[]`: `id`, `kind` (`gravity` | `point-force` | `moment`), `target` (assembly body, hardware id, or assembled frame), `magnitude`, `units`, `safety_factor` >= 1, `source`. Moment loads declare `section.outer_parameter` and `section.inner_parameter` naming `dimensions[].parameter`. Load `source` cannot be `assumed`.

`sim.scene`: named id `table-flat` or `floor-generic` (or a prefix of either), `gravity_mm_s2`, `floor.z_mm`, `friction.mu` with `source`. Not a photoreal house.

`sim.calibration[]` is ignored when absent. Each coupon has `id`, `type` (`mass` | `friction` | `actuator`), `magnitude`, `units`, and `source` (`measured` | `datasheet` | `fit-tested` | `assumed`). Mass targets a printed body. Friction names a scene. Actuator `kind` is `stall_torque` or `free_run_rpm` and targets hardware or a joint. `sim.sim2real: true` is allowed only when mass, friction, and actuator coupons exist with `measured` or `datasheet` sources; `assumed` (and `fit-tested` alone) cannot claim sim2real. Markdown / MJCF / URDF / USD cannot grant the claim.

`sim.roll` when present records a commanded `distance_mm` on a named scene plus optional `sim_mm`, `bench_mm`, and `error_budget_mm`.

A robot-module that declares `assembly.bodies` fail-closes unless every printed STL body appears, every assembly ref resolves, every revolute joint has limits, and required loads exist (gravity, plus a stall moment targeting each revolute child).

## Proof boundary

The contract describes intent. It does not prove geometry. After export, `validate_project.py` independently verifies:

1. spec is complete and files exist
2. each CAD parameter is declared in source
3. each STL parses, is watertight, and has positive signed volume
4. shell count matches the spec
5. exported shells do not occupy the same space
6. bounding box fits strictly inside the machine envelope
7. overhang and class-specific DFM heuristics
8. sampled wall thickness vs `geometry.min_wall_mm` (`thin_wall_area_frac=0.02`)

When `assembly` is present, `validate_assembly.py` then places printed STLs and hardware envelopes at the declared poses and fail-closes on illegal occupancy, joint self-collision, and missing or assumed required loads. A render or simulator window is not proof.

A preview is not proof. An STL that opens is not proof. `HARD=0` is necessary; visual inspection and fit evidence are still required.
