# robot-kit-01-rover

Narrative only. The machine contract is `PRINT_SPEC.yaml`.

Numbered 01 two-wheel differential chassis in the photo-class micro-robotics kit: MCU on deck, dome head with LED pass-through, bought N20-class drive units. Print chassis, two wheels from one STL, and head. Do not print the MCU, motors, battery, or driver.

Shared kit library: `src/lib/robot_kit.scad` (MCU pocket, SG90 pocket, M2/M3, 3-spoke hub).

Sim2real claim is on `PRINT_SPEC.yaml` (`sim.sim2real`, mass/friction/actuator coupons). Commanded table-flat roll is 100 mm; measured bench roll 87 mm; error budget 20 mm. This paragraph is not parsed.

Preview-only assembly (not a printable body, not in `geometry.stl_files`).
`src/rover.scad` accepts `-D which="assembly"` in desktop OpenSCAD. Headless stills:

```bash
python3 examples/robot-kit-01-rover/scripts/render_assembly.py
```
