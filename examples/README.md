# Examples

`bracket-coupon` is a printable L-bracket coupon (40×30 mm L, 12 mm thick) with M3-class holes. It demonstrates `PRINT_SPEC.yaml` plus OpenSCAD without publishing private geometry.

```bash
python3 skills/3d-print-design-brief/scripts/validate_print_spec.py \
  examples/bracket-coupon/docs/PRINT_SPEC.yaml

docker run --rm -v "$PWD/examples/bracket-coupon:/work" -w /work \
  openscad/openscad:2021.01 \
  openscad -o /work/stl/bracket-coupon.stl --export-format=binstl \
  /work/src/bracket-coupon.scad

python3 skills/3d-print-validate/scripts/validate_project.py \
  examples/bracket-coupon
```

CI sample prompts export this STL (and the other prompt STLs) as the `generated-stls` artifact.

`bracket-coupon-vibecad` is the same 40×30×12 mm coupon with `cad.backend: vibecad` and a VibeScript/Part CSG `.py`. Default CI does not run VibeCAD: it checks the spec, named parameters, and the committed STL with `validate_project`. Live OCC export is extra extra when `VIBECAD_CMD` is set.

```bash
python3 skills/3d-print-design-brief/scripts/validate_print_spec.py \
  examples/bracket-coupon-vibecad/docs/PRINT_SPEC.yaml

python3 skills/3d-print-validate/scripts/validate_project.py \
  examples/bracket-coupon-vibecad
```

`robot-kit-01-rover` is a numbered-01 two-wheel `robot-module` chassis (MCU on deck, LED head). Motors, MCU, battery, and driver are bought.

```bash
python3 skills/3d-print-design-brief/scripts/validate_print_spec.py \
  examples/robot-kit-01-rover/docs/PRINT_SPEC.yaml

python3 skills/3d-print-validate/scripts/validate_project.py \
  examples/robot-kit-01-rover

python3 examples/robot-kit-01-rover/scripts/render_assembly.py
```

`robot-kit-01-rover-v2` is the same numbered-01 chassis family with an SG90 pan, HC-SR04 on a printed bracket, and an MPU-6050 pad. Motors, MCU, servo, sensors, battery, and driver are bought.

```bash
python3 skills/3d-print-design-brief/scripts/validate_print_spec.py \
  examples/robot-kit-01-rover-v2/docs/PRINT_SPEC.yaml

python3 skills/3d-print-validate/scripts/validate_project.py \
  examples/robot-kit-01-rover-v2

python3 skills/3d-print-validate/scripts/validate_assembly.py \
  examples/robot-kit-01-rover-v2

python3 examples/robot-kit-01-rover-v2/scripts/render_assembly.py
```

`robot-kit-01-rover-kid` is the same v2 kit enclosed in a rounded hull and lid so the boards, motors, servo, and wiring are not visible. The pan head is a visor face (HC-SR04 as eyes). Toy wheels use a capped hub.

```bash
python3 skills/3d-print-design-brief/scripts/validate_print_spec.py \
  examples/robot-kit-01-rover-kid/docs/PRINT_SPEC.yaml

python3 skills/3d-print-validate/scripts/validate_project.py \
  examples/robot-kit-01-rover-kid

python3 skills/3d-print-validate/scripts/validate_assembly.py \
  examples/robot-kit-01-rover-kid

python3 examples/robot-kit-01-rover-kid/scripts/render_assembly.py
```


