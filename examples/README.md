# Examples

`bracket-coupon` is a generic 40×30×12 mm parametric brick. It demonstrates `PRINT_SPEC.yaml` plus OpenSCAD without publishing private geometry.

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
