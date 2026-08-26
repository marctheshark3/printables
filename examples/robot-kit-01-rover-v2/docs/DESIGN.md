# robot-kit-01-rover-v2

Narrative only. The machine contract is `PRINT_SPEC.yaml`.

Numbered 01 rover revision: same ESP32-C3 Super Mini pocket and N20 drive as v1, plus an SG90 pan, an HC-SR04 on a printed bracket (forward +X), and an MPU-6050 class IMU pad on the deck. Print chassis, two wheels from one STL, and the sensor bracket. Do not print the MCU, motors, servo, IMU, ultrasonic, battery, or driver.

Shared kit library: `src/lib/robot_kit.scad`.

Sim2real claim is on `PRINT_SPEC.yaml` (`sim.sim2real`, mass/friction/actuator coupons). Commanded table-flat roll is 100 mm; measured bench roll 86 mm; error budget 20 mm. This paragraph is not parsed.

Preview-only assembly stills (not a printable body, not in `geometry.stl_files`):

```bash
python3 examples/robot-kit-01-rover-v2/scripts/render_assembly.py
```

