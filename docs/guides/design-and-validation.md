# Design and validation

[Documentation](../README.md) · [Getting started](../getting-started.md)

Run commands from the repository root, with `PROJECT` set to your part's directory.

```text
PRINT_SPEC.yaml → Parametric CAD → One STL per body → Project validation
                                                    → Assembly validation, when declared
```

## Define the contract

Write `docs/PRINT_SPEC.yaml` inside the project before building CAD. [`3d-print-design-brief`](../../skills/3d-print-design-brief/SKILL.md) defines the contract; the [PRINT_SPEC reference](../../skills/3d-print-design-brief/references/print-spec-v1.md) documents its fields.

Each project declares:

- Parametric CAD (`cad.parametric: true`), millimetres, and Z-up.
- A named CAD parameter, nominal value, tolerance, and provenance for every critical dimension.
- Explicit X/Y/Z printer build volume, minimum wall thickness, and minimum feature sizes.
- One STL per independently printed body, with an expected watertight shell count and no overlapping exported solids.
- Clearance per side, fit evidence, and a coupon policy.
- Print orientation, bed face, supports policy, and overhang limit.
- Service material and drainage requirements.

```bash
python3 skills/3d-print-design-brief/scripts/validate_print_spec.py \
  "$PROJECT/docs/PRINT_SPEC.yaml"
```

The validator must exit 0. An assembly has several `geometry.stl_files` entries. `docs/DESIGN.md` is narrative only and is never parsed. Assumed critical fits cannot ship. After a required fit coupon is printed, [the design brief](../../skills/3d-print-design-brief/SKILL.md) records the caliper value with `record_fit.py`.

## Choose CAD

VibeCAD is the dimensional kernel ([10-X-eng/vibecad](https://github.com/10-X-eng/vibecad)). It is a separate project from the PyPI package named `vibecad`; upstream FreeCAD is not a supported substitute kernel. See [backend setup](../getting-started.md#set-up-a-cad-backend).

| Geometry or task | Backend |
|---|---|
| Dimensional mechanical part | `vibecad` |
| CI sample export, a request naming OpenSCAD, or a host where VibeCAD cannot run | `openscad` |
| Organic or lattice body | `blender` |
| Separate bodies owned by different backends | `hybrid` |
| Optional reverse reconstruction through CadQuery | `cadquery` |

OpenSCAD is not the dimensional kernel. Hybrid means separate declared bodies, with each body owned by one backend. Every backend must pass the same validator after export.

For an organic Blender example:

```bash
skills/3d-print-blender/scripts/pblend new organic-lid --class enclosure
skills/3d-print-blender/scripts/pblend run --project "$HOME/print-projects/organic-lid"
skills/3d-print-blender/scripts/pblend gate --project "$HOME/print-projects/organic-lid"
```

VibeCAD boolean welding of overlapping solids remains a known limit until a live export proves one solid. See [project status](../status.md#known-limits) for backend limitations.

## Validate exported bodies

```bash
python3 skills/3d-print-validate/scripts/validate_project.py "$PROJECT"
```

Delivery requires `HARD=0`. The validator blocks:

- Incomplete or contradictory contracts, missing source or STL, and unsafe project paths.
- Non-parametric backend declarations or missing named CAD parameters.
- Open, non-manifold, inconsistently oriented, duplicate, or degenerate mesh topology.
- Wrong connected-shell counts, overlapping exported solids, or non-positive volume.
- Build-volume overflow, unacceptable fit or wet-service evidence, and class-specific overhang or open-under failures.
- Sampled wall thickness below `geometry.min_wall_mm` over more than `thin_wall_area_frac=0.02` of sampled area, allowing 0.05 mm tessellation slack.

Thickness uses sampled inward rays, so it is not an exact-kernel proof. Short STL chords are tessellation and remain warning-only. Each CAD backend must also validate its final solid before export.

## Validate assemblies and robotics

When `assembly` is present, run the assembly gate after project validation:

```bash
python3 skills/3d-print-validate/scripts/validate_assembly.py "$PROJECT"
```

It must report `HARD=0` for assembled occupancy, joint self-collision, and required load evidence. A render or simulator window is not proof.

The [rover examples](../../examples/README.md) are the numbered-01 kit family: the base chassis, v2 with sensors, and the kid hull. Print the chassis, wheels, and brackets; buy motors, boards, batteries, and servos.

```bash
python3 skills/3d-print-validate/scripts/validate_project.py \
  examples/robot-kit-01-rover
python3 skills/3d-print-validate/scripts/validate_assembly.py \
  examples/robot-kit-01-rover
python3 skills/3d-print-sim/scripts/roll_table_flat.py \
  examples/robot-kit-01-rover
```

The same validators apply to `examples/robot-kit-01-rover-v2` and `examples/robot-kit-01-rover-kid`. A `sim2real: true` claim requires mass, friction, and actuator coupons from measurements or datasheets; assumed calibration cannot support it.

## Inspect and deliver

Use [`3d-print-cad-render`](inspection-and-instructions.md) for STEP inspection, then [pack and slice](pack-and-slice.md). Inspect every body in print orientation and in the slicer. Validation and rendering do not authorize a live print.
