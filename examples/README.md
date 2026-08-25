# Examples

`bracket-coupon` is a fake 40×30×12 mm envelope plus the stock `part_scaffold.scad`. It exists so the public repo can show the DESIGN.md ↔ SCAD pair without shipping household geometry.

```bash
python3 skills/openscad-printables/scripts/dfm_gate.py \
  --project examples/bracket-coupon \
  --stl /path/to/exported.stl \
  --mode-file examples/bracket-coupon/docs/DESIGN.md
```

Export still needs Docker OpenSCAD; CI does not run that path.
