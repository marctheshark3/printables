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

When `assembly` is present, `validate_assembly.py` then places printed STLs and hardware envelopes at the declared poses and fail-closes on illegal occupancy, joint self-collision, and missing or assumed required loads. A render or simulator window is not proof.

A preview is not proof. An STL that opens is not proof. `HARD=0` is necessary; visual inspection and fit evidence are still required.
