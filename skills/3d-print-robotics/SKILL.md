---
name: 3d-print-robotics
description: Design numbered FDM micro-robotics kit modules.
version: 1.0.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [3d-print, robotics, robot, module, kit, rover, mcu, servo, numbered, chassis, wiring, hardware, openscad, fdm]
    related_skills: [3d-print-design-brief, 3d-print-openscad, 3d-print-validate, 3d-print-sim]
---

# 3D Print Robotics

Class skill for **numbered micro-robotics kit modules** (01 two-wheel rover, 02 servo gripper, 03 gimbal). CAD backend default = **OpenSCAD**. Not a firmware repo, not ROS, not custom PCB layout.

## When to use

- Numbered kit module with a shared MCU family
- Two-wheel rover chassis, servo gripper arm, or gimbal joystick body
- MCU pocket, motor/servo pockets, fastener bosses, cable-path keepouts
- PRINT_SPEC `product_class: robot-module` with hardware BOM and wiring pin map

**Don’t:** print motors, batteries, MCUs, servos, bearings, or extrusion frames; live motor firmware; Blender as the dimensional backend; a second contract besides `PRINT_SPEC.yaml`.

## Hard sequence

1. **3d-print-design-brief** → `docs/PRINT_SPEC.yaml` (`product_class: robot-module`)
2. **hardware/wiring contract** — non-empty `hardware.components` BOM; `wiring` voltage_domains, pin_map or nets, connector keepouts, named cable-path keepouts mapped to CAD parameters
3. **OpenSCAD bodies** from `lib/robot_kit.scad` (MCU pocket, servo/motor pockets, M2/M3, wheel hub)
4. **export** one STL per independently manufactured printed body
5. **`validate_project.py`** — HARD fail means redesign, not a relaxed gate
6. **`validate_assembly.py`** when `assembly` is present — occupancy, joint sweep, required loads; a render is not proof

## Geometry laws (session-hard)

| Law | Detail |
|-----|--------|
| MCU pocket | Super Mini class pocket + USB keepout; datasheet or measured; never `assumed` |
| Servo/motor pockets | SG90/9g or N20-class wells with named clearance; horn/shaft swing kept clear |
| Fastener bosses | Shared M2/M3 through-hole and boss library so 01/02/03 share one board family |
| Cable channels | Named keepouts from `wiring.cable_path_keepouts` become CAD parameters |
| One body / STL | No overlapping exported bodies; `overlapping_solids_allowed: false` |
| OpenSCAD default | Dimensional kit bodies in OpenSCAD; Blender only for an organic skin |

## Numbered-kit rule

Modules **01 / 02 / 03** share one MCU-pocket family and the M2/M3 fastener library in `lib/robot_kit.scad`. Copy that file into each project `src/lib/` for hermetic Docker export. USB window sizes live in `3d-print-openscad/references/connector-keepouts-fdm.md` — do not duplicate that table.

## Buy vs print

Buy: motors, batteries, MCUs, servos, bearings, extrusion frames, motor drivers.
Print: chassis, wheels, heads, horns-adjacent brackets, fastener bosses, cable-path walls.

## Gold

`examples/robot-kit-01-rover/` — numbered 01 two-wheel differential chassis, MCU on deck, LED head.

`examples/robot-kit-01-rover-v2/` — same MCU/N20 family plus SG90 pan, HC-SR04 bracket, IMU pad.

`examples/robot-kit-01-rover-kid/` — enclosed hull/lid of v2; visor head, capped toy wheels.

## Pitfalls

1. Assumed MCU or servo pocket (HARD)
2. Empty hardware BOM on robot-module (HARD)
3. 3V3 and 5V claimed on the same net or MCU pin (HARD)
4. Printing the motor, battery, or board
5. Combining chassis + wheels into one exported solid
6. A second wiring spreadsheet that is not PRINT_SPEC.yaml

## Done when

Gated robot-module spec + one STL per printed body + hardware/wiring + `validate_project.py` HARD=0. When `assembly` is declared, `validate_assembly.py` HARD=0 as well.
