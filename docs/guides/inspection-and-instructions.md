# Inspection and instructions

[Documentation](../README.md) · [Skill catalog](../../skills/README.md#review-and-instructions)

Run commands from the repository root, with `PROJECT` set to the part's directory. Inspection uses STEP geometry or an existing OCC scene dump.

## Open the CAD inspector

[`3d-print-cad-render`](../../skills/3d-print-cad-render/SKILL.md) is the pack's CAD inspector: parts tree, measurement in world millimetres, OCC faces, and BREP edges.

```bash
export QT_QPA_PLATFORM=offscreen
export FREECAD_CMD=/path/to/FreeCADCmd
python3 skills/3d-print-cad-render/scripts/render_cad_project.py \
  --project "$PROJECT" --serve --port 8107
```

Open `http://127.0.0.1:8107/?view=solid`. The page should load, list the study in the parts tree, and report measurements in millimetres.

With an existing OCC dump, packing the viewer does not need the CAD binary:

```bash
python3 skills/3d-print-cad-render/scripts/render_cad_project.py \
  --scene scene.json --out-dir "$PROJECT/renders/cad-inspector"
```

The inspector serves on loopback only. The pack ships neither a network proxy nor a FreeCAD binary. `./install.sh` does not copy this skill, preserving any profile-local inspector. Use it from this checkout when needed.

An STL preview is not a CAD inspection. The inspector does not edit geometry or approve printing; use the [validation workflow](design-and-validation.md) for the required checks.

## Choose an instruction style

| Need | Skill | Output |
|---|---|---|
| Picture-led build sheets or blueprints | [3d-print-lego-instructions](../../skills/3d-print-lego-instructions/SKILL.md) | `instructions.html` or the inspector's Instructions overlay |
| A required assembly sequence | [3d-print-ikea-instructions](../../skills/3d-print-ikea-instructions/SKILL.md) | `ikea.html`, one solid per step |

A named style wins. If the request leaves it unclear whether a single required sequence is intended, clarify before producing a required-sequence booklet. The inspector's Instructions button always opens the picture sheet.

Lego-style edge-art booklet from an OCC dump:

```bash
python3 skills/3d-print-lego-instructions/scripts/render_booklet.py \
  scene.json --out instructions.html --title "Assembly"
```

The output includes the order rule `centroid z, then y, then x, then name`. Identical parts inside a 2 mm Z band can share a callout. The inspector button uses the same ordering with shaded snapshots.

Required-sequence booklet:

```bash
python3 skills/3d-print-ikea-instructions/scripts/render_ikea_booklet.py \
  scene.json --out ikea.html --title "Assembly"
```

The output includes `This sequence is required` and one step per solid. If the user supplied an order, use the skill's `--order` option. IKEA steps never batch identical solids.

Centroid order is not a fastener or mate plan. Presenting one sequence as required does not prove another order fails. These are neither LDraw exports nor official LEGO or IKEA manuals, and they do not approve printing.

## Example: butterfly habitat

These stills use the public [butterfly habitat](https://github.com/marctheshark3/butterfly-habitat) kit, arranged as that repository's viewer compound places its panels. The project itself is not vendored here.

![CAD inspector showing the butterfly habitat](../images/butterfly-inspector.png)

![Assembly sheets for the butterfly habitat](../images/butterfly-instructions.png)

The sheets show steps 1, 4, and 10. Step 4 places two side frames. The sequence illustrates centroid ordering, not a verified fastener plan or print approval.
