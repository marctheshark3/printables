# Headless Blender gotchas (Spark)

## Always

- Run scripts with `blender -b -P script.py -- args…` or `pblend run`
- Host `python3` **does not** have `bpy`
- Args for the script go **after** `--`

## Env (set by pblend)

| Var | Meaning |
|-----|---------|
| `PBLEND_PROJECT` | Project root |
| `PBLEND_LIB` | Skill `scripts/` (import `bpy_lib`) |
| `PBLEND_SKILL` | Skill root |
| `BLENDER` | Override binary |
| `DFM_GATE` | Override dfm_gate.py path |

## Deps

- Blender ships its own Python (3.12 on 4.0.2 here) + numpy
- scipy may be present (gold Voronoi needs it) — `pblend doctor` reports
- Do not `pip install` into system expecting bpy

## Previews

- WORKBENCH &gt; EEVEE on headless
- Empty PNG ≠ success — fall back to STL→numpy+PIL multiview (openscad-printables `references/stl-pil-multiview.md`)

## Export API

- Blender 4.0: `bpy.ops.export_mesh.stl(...)`
- Import may be `bpy.ops.wm.stl_import` or legacy `import_mesh.stl` — preview runner tries both

## Performance

- Keep bevel/boolean segments modest (8–24)
- EXACT boolean on dense Voronoi can take tens of seconds — OK; hang &gt; few minutes → simplify
