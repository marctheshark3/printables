# Preview pattern: legible STL review (Marc)

Sparse matplotlib “fishnet” isos are **not enough**. Marc will say the preview is too hard to tell if the design is what he wants.

## Ship both

1. **Interactive hub viewer** (primary judgment tool)
   - Single-file HTML: three.js r160+ modules from unpkg (`three`, `OrbitControls`, `STLLoader`, optional `RoomEnvironment`)
   - Co-locate HTML + STL under `~/Documents/wiki/wiki/outputs/<project>/`
   - Load STL via relative URL: `new URL('part.stl', window.location.href)`
   - Wiki hub serves binary STL raw under `/view/wiki/outputs/...` (header starts with `OpenSCAD Model` or binary facet data)
   - Controls: drag orbit, scroll zoom, right-drag pan
   - Preset buttons: iso / top / under / rear / side
   - Rotate mesh `x = -π/2` if OpenSCAD Z-up → Three Y-up
   - Material: MeshPhysicalMaterial (slight clearcoat), dark studio bg, key+fill+rim lights
   - Hub URL via `wiki-view-url.py --hub-only <html>`

2. **Solid multi-view stills** (Discord attachments)
   - Normal-based lighting (ambient + directional), solid faces, dark `#0b0d10` bg
   - Contact sheet: iso, top, front, side, rear, underside
   - Cutaway (half mesh by centroid) to show print-in-place understructure
   - Optional chassis ghost box for scale
   - Attach heroes via `MEDIA:` absolute PNG paths
   - **Under view is first-class** when elevated/PIP structure exists

## Avoid

- Single low-res edge-heavy iso as the only deliverable
- **Wireframe / fishnet-only** matplotlib (black edges, no solid faces)
- Elevated-deck designs **without a solid under view** (pin forests hide here)
- Blocking on OpenSCAD `--camera` PNG headless (needs DISPLAY/OpenGL; often empty on Spark Docker)

## Matplotlib solid recipe (Spark)

- `Poly3DCollection(..., linewidths=0)`; `set_edgecolor('none')`
- Dual directional lights on face normals → solid face colors
- Dark bg `#0b0d10`; always include **under** + cut_x/cut_y when PIP structure exists
- Fail preview gate if underside reads as unexplained pins or pure edge noise

## Reference implementation (skill gold)

DGX Spark stand **v9 open frame**:

- `docs/preview-3d.html` (interactive)
- `renders/v9_hero_*.png` + `renders/v9_contact_sheet.png`
- Under view must prove **empty midspan** (not pins/waffle)
- Optional ghost chassis 150×150×50.5 for proportion

Hub (when served): `(private local hub — not published)`

Skill regression: `references/regression-test-stand.md` gates G9/S5.
