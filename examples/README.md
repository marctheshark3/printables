# Examples

`bracket-coupon` is a generic 40×30×12 mm parametric scaffold. It demonstrates the authoritative `PRINT_SPEC.yaml` plus an OpenSCAD source file without publishing private geometry.

Validate the contract:

```bash
python3 skills/3d-print-design-brief/scripts/validate_print_spec.py \
  examples/bracket-coupon/docs/PRINT_SPEC.yaml
```

After exporting the declared STL, validate the complete project:

```bash
python3 skills/3d-print-validate/scripts/validate_project.py \
  examples/bracket-coupon
```

The second command intentionally fails until `stl/bracket-coupon.stl` exists. Missing output is not a warning.
