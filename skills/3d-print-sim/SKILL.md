---
name: 3d-print-sim
description: Prove assembled robot-module fit from PRINT_SPEC.
version: 1.0.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [3d-print, assembly, sim, joints, occupancy, loads, clearance, robot-module, kit, rover, validate, table-flat, mjcf, calibration, sim2real, mass, friction, actuator, roll]
    related_skills: [3d-print-design-brief, 3d-print-robotics, 3d-print-openscad, 3d-print-validate]
---

# 3D Print Sim

Fail-closed assembled occupancy for numbered `robot-module` kits. Simulation is a validator, not a CAD kernel. OpenSCAD remains the dimensional default. A MuJoCo window or screenshot is not proof.

## When to use

- Numbered kit that must be shown to fit and move before print
- `assembly.bodies`, `assembly.joints`, `loads`, or `sim.scene` on PRINT_SPEC
- Wheel/chassis clearance, joint sweep, stall moment at a hub
- `sim.calibration` mass/friction/actuator coupons and a `sim2real` claim

**Don’t:** treat a render as proof; parse MJCF/URDF/USD/Markdown as the contract; add ROS, Isaac, or Gazebo as a hard dependency; relax mesh HARD gates so occupancy can pass; claim sim2real from assumed coupons.

## Hard sequence

1. **3d-print-design-brief** — `docs/PRINT_SPEC.yaml` with assembly poses (mm/deg), joints, loads
2. **3d-print-robotics / 3d-print-openscad** — one STL per independently manufactured body
3. **`validate_project.py`** — mesh gates first; HARD still blocks delivery
4. **`validate_assembly.py`** — L1 occupancy and mate clearance; L2 joint sweep; L3 handbook-style hub section vs PETG allowable × `safety_factor`

```bash
python3 skills/3d-print-validate/scripts/validate_project.py "$PROJECT"
python3 skills/3d-print-validate/scripts/validate_assembly.py "$PROJECT"
```

Exit 0 only when HARD=0. Wheels may spin in their bore; they may not intersect the chassis.

## Optional emit

`scripts/emit_mjcf.py` writes MJCF (and URDF) *from* the spec + STL paths for later sim2real. One-way. Never parse the emit back as PRINT_SPEC.

`sim2real: true` is a PRINT_SPEC claim. It requires mass (printed body on a scale), friction (sled on `table-flat` or `floor-generic`), and actuator (stall torque or free-run RPM) coupons with `measured` or `datasheet` sources. Assumed calibration cannot claim sim2real.

Optional extra extra (skipped if `mujoco` is absent):

```bash
python3 skills/3d-print-sim/scripts/roll_table_flat.py "$PROJECT"
```

## Pitfalls

1. Assumed joint limits or stall load (HARD)
2. Assembly body id that is not a printed STL body or hardware component id (HARD)
3. Missing gravity or hub stall on a robot-module that declares assembly (HARD)
4. Using a simulator screenshot in place of `validate_assembly.py`

## Done when

`validate_print_spec.py`, `validate_project.py`, and `validate_assembly.py` all exit 0 on the project.
