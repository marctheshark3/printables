---
name: 3d-print-lego-instructions
description: Build Lego-style assembly sheets from a mill STEP.
version: 0.1.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [lego, instructions, booklet]
    related_skills: [3d-print-cad-render, 3d-print-vibecad]
---

# Lego-style assembly sheets

Printable build sheets from a mill STEP: a step number, the parts placed so far, and a callout for what is new. Order is centroid z, then y, then x, then name. Not an LDraw model, not a LEGO Group manual, and not print approval.

The planner and the SVG booklet are stdlib Python. The inspector Instructions button uses the same order and draws shaded snapshots from the loaded study. This skill does not call LPub3D, Studio, Lic, or BrickStep. Those read LDraw, not STEP.

## When to Use

- "Lego instructions" / "building instructions from the CAD" / "step sheet"
- the mill STEP is done and you want a printable assembly sequence
- the CAD inspector is open and the sheet should come from the loaded solids

**Don't:** approve a print, slice, convert solids into bricks, or treat one solid as a multi-step brick build.

## Prerequisites

- An OCC dump (`source` is `occ-step` or `occ-brep`) with `vertices` and BREP `edges`, or a loaded inspector study
- Host `python3` (stdlib only) for `scripts/render_booklet.py`
- The Instructions button needs `viewer/app.js` bundled into `viewer.bundle.js` after that file changes

## How to Run

From the pack root, invoke through the `terminal` tool:

```bash
python3 skills/3d-print-lego-instructions/scripts/render_booklet.py \
  scene.json --out instructions.html --title "Assembly"
```

Plan only:

```bash
python3 skills/3d-print-lego-instructions/scripts/plan_steps.py scene.json
```

Loopback inspector: open the study at `http://127.0.0.1:8107/?view=solid`, then the toolbar button `instructions`. That button does not call this script. It plans from the loaded meshes and opens a printable overlay.

## Quick Reference

- `scripts/plan_steps.py` — order and grouping, JSON on stdout
- `scripts/render_booklet.py scene.json --out instructions.html`
- Order rule: `centroid z, then y, then x, then name`
- `Z_BAND_MM = 2` — identical fingerprints in that band share a step
- Fingerprint: tenth-millimetre bbox, vertex count, color (missing color is `#c4b49a`)
- New-part stroke: `#c42b23`. Previous-part stroke: `#1c1b18`
- Button id: `instructions`
- Page note: `Not an LDraw model. Not print approval.`

## Procedure

1. Resolve an OCC dump. No dump and no loaded study → stop. An STL mesh source is a hard fail.
2. Plan steps with `plan_steps.py`. Completion: step 1 is the lowest centroid Z, and a single solid is exactly one step.
3. Write `instructions.html` with `render_booklet.py`. Completion: the file contains the order rule, a BOM sheet, and one `data-step` per step.
4. In the inspector, click Instructions. Completion: a white overlay, one sheet per step, a black step number, a shaded view of placed solids, and a callout marked `N×`.
5. Print the overlay or the HTML to PDF from the browser. This pack does not ship a PDF compiler.
6. Do not treat the sheet as print approval. That gate is `3d-print-validate`.

## Pitfalls

1. LPub3D, Studio, Lic, and BrickStep read LDraw. They cannot ingest this STEP.
2. OSH Automated Documentation can annotate a STEP in FreeCAD and compile a PDF. That is a manual camera and step pass. It is not this button, and this pack does not vendor it.
3. Centroid order is not a mate, fastener, or removal planner. Exploded X offsets in the inspector are not the build order.
4. A 2 mm Z band groups parts with the same size, vertex count, and color. Mirrors can share one callout. The main view still shows each placement.
5. One solid is one sheet. Do not invent sub-steps.
6. The script booklet is isometric BREP edge art. The button booklet is a shaded snapshot. Same order, not the same pixels.
7. `./install.sh` copies this skill and does not copy `3d-print-cad-render`. A profile-local inspector does not gain the button from install.
8. Do not write a hostname, home path, or Tailscale URL into this tree.

## Verification

- [ ] `python3 -m pytest -q skills/3d-print-lego-instructions/tests` passes
- [ ] `instructions.html` contains `centroid z, then y, then x, then name` and `Not an LDraw`
- [ ] Step 1 omits solids whose centroid Z is higher
- [ ] Inspector template has `id="instructions"`
- [ ] Diff has no `/home/` and no Tailscale hostname
