# robot-kit-01-rover-kid

Narrative only. The machine contract is `PRINT_SPEC.yaml`.

Kid-friendly enclosure of numbered-01 rover v2: same ESP32-C3 Super Mini, N20 drive, SG90 pan, HC-SR04, and MPU-6050. A rounded hull and lid hide the MCU, IMU, motors, servo, and cable paths. Toy wheels use a capped hub so the D-shaft is not visible from outside. The pan head is a visor face; the two transducers are the eyes.

Print chassis, lid, two wheels from one STL, and head. Do not print the MCU, motors, servo, IMU, ultrasonic, battery, or driver.

Shared kit library: `src/lib/robot_kit.scad`.

Sim2real claim is on `PRINT_SPEC.yaml` (`sim.sim2real`, mass/friction/actuator coupons). Commanded table-flat roll is 100 mm; measured bench roll 84 mm; error budget 20 mm. This paragraph is not parsed.

Preview-only assembly stills (not a printable body, not in `geometry.stl_files`):

```bash
python3 examples/robot-kit-01-rover-kid/scripts/render_assembly.py
```
