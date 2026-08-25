# bpy FDM patterns (P1S)

## Units + orientation

- mm, Z-up
- Document `print_orientation` + `use_flip` in DESIGN.md
- Feet-down default; lid lattices often print lattice-on-bed then flip for use

## Min feature

- Walls / webs ≥ **1.6 mm** (prefer 1.8–2.2 for lattices)
- Pins root in **solid corner pads**, not thin webs
- Chamfers/bevels ≤ 45° language when possible

## Booleans

- Prefer `BOOLEAN` solver **EXACT** for printables
- Apply modifiers before STL export
- Remove doubles + consistent normals after difference
- Cutter objects deleted after apply

## Lattices

- Build as **wall skeleton** (union of web capsules) not random solidify-on-wire
- Avoid Solidify on open non-manifold curves (explode)
- Frame margin + corner pads keep one welded shell

## Export

```python
from bpy_lib.scene import export_stl, mesh_stats
mesh_stats(obj)
export_stl(obj, out_dir / "part.stl")  # binary, scale 1.0, selection-only
```

## Multi-body

- Export printable halves separately (`base`, `lid`)
- `assembly` STL = preview only — `pblend gate` skips `*assembly*`
