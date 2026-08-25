# Gold: hybrid Pi Zero noloop print pack

**Path:** `~/Documents/the-grid/rpi-zero-print-noloop`  
**Status:** v1.0.0 — **print this**

| STL | Source |
|-----|--------|
| `rpi-zero-noloop-base.stl` | OpenSCAD honeycomb, `enable_keyring=false` |
| `rpi-zero-noloop-lid.stl` | Blender hex plate (`rpi-zero-voronoi-noloop` v0.5) |

## Rebuild

```bash
# Base
docker run --rm -v "$HOME/Documents/the-grid:/data" openscad/openscad:2021.01 \
  openscad -o /data/rpi-zero-print-noloop/stl/rpi-zero-noloop-base.stl \
  -D 'which="base"' -D 'enable_keyring=false' \
  /data/rpi-zero-honeycomb-case/src/rpi-zero-honeycomb-case.scad

# Lid
PBLEND=~/.hermes/profiles/tron/skills/creative/blender-printables/scripts/pblend
"$PBLEND" run --project ~/Documents/the-grid/rpi-zero-voronoi-noloop --which lid
cp ~/Documents/the-grid/rpi-zero-voronoi-noloop/stl/rpi-zero-voronoi-noloop-lid.stl \
  ~/Documents/the-grid/rpi-zero-print-noloop/stl/rpi-zero-noloop-lid.stl

"$PBLEND" preview --project ~/Documents/the-grid/rpi-zero-print-noloop
"$PBLEND" gate --project ~/Documents/the-grid/rpi-zero-print-noloop
"$PBLEND" pack --project ~/Documents/the-grid/rpi-zero-print-noloop --version v1.0.0
```

## Gate note

Organic lids may need `--thin-fail-frac 0.35` or DESIGN `gate_override` for tessellation short edges (same as honeycomb case). Still vision-check stills.
