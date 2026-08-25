---
name: image-silhouette-print
description: "Use when turning an icon/image into a 3D-printable silhouette part (stencils, cookie cutters, ornaments). Image is design authority; CAD only shells + DFM. Overlay QA before extrude."
version: 1.0.0
author: Tron
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [silhouette, stencil, image-trace, openscad, 3d-print, icon, fdm, bambu]
    related_skills: [openscad-printables, printables-dfm-gate, printables-part-brief]
---

# Image → Silhouette → Print

## Overview

**Iconographic FDM.** The image (generated or user-supplied) is the design authority. CAD only applies the mechanical shell: plate/frame, thickness, hole policy, bridges, DFM.

Do **not** sculpt organic icons with OpenSCAD hull/circles. That path fails icon literacy (see water-stencils CAD mermaid/unicorn).

Sibling to `openscad-printables` — not a merge. Hand off STL to `printables-dfm-gate`.

## When to Use

- Water/sand stencils, cookie cutters, ornaments, icon coasters, kid puzzle silhouettes
- User wants recognizable character/object cutouts
- Compare/contrast vs pure CAD sculpt
- User provides PNG/SVG or asks to generate a silhouette

**Don’t use for:** mechanical brackets, equipment stands, anything whose source of truth is calipers (use printables-part-brief + openscad-printables).

## Hard sequence

```
1. Lock plate envelope + hole_policy in docs/DESIGN.md
2. Source icon (gen under prompt contract OR user PNG)
3. scripts/trace_silhouette.py → binary + polygon (mm) + SVG audit
4. scripts/overlay_preview.py → plate frame + silhouette PNG
5. HUMAN/agent QA gate — accept overlay BEFORE extrude
6. scripts/scad_from_poly.py → OpenSCAD wrapper + Docker STL
7. printables-dfm-gate on STL
8. Zip + print notes; optional compare pack vs CAD path
```

**HARD: no STL claim until overlay accepted.**

## Prompt contract (image gen)

When generating:

- Flat **solid black** filled silhouette on **pure white** background
- **No** gradients, outlines-only, shading, text, watermark
- **No internal holes** unless hole_policy allows (default filled)
- Single subject, centered, margin ~8–12%
- View locked: side-profile | top-down | front (state in DESIGN.md)
- Toddler-icon bold shapes; avoid hair-thin features
- IP: generate or user art only — never trace trademark characters

## Hole policy

| Policy | Behavior |
|--------|----------|
| `filled` | Fill interior holes; one outer contour (water stencils default) |
| `islands-bridged` | Keep holes; add ≥ min_feature bridges to frame/body |
| `islands-loose` | Forbidden for toddler loose parts |

## Envelope defaults (water stencil class)

| Param | Default |
|-------|---------|
| plate_mm | 160 |
| thickness_mm | 2.0 |
| frame_mm | 14 |
| corner_r_mm | 10 |
| min_feature_mm | 1.6 |
| print_orientation | feet-down |
| product_class | other |

## Scripts (this skill)

```bash
SKILL=~/.hermes/profiles/tron/skills/creative/image-silhouette-print

# 1) Trace PNG → poly JSON + binary PNG + SVG
python3 "$SKILL/scripts/trace_silhouette.py" \
  --input path/to/icon.png \
  --out-dir project/trace/name \
  --plate 160 --frame 14 \
  --min-feature-mm 1.6 \
  --hole-policy filled \
  --components largest   # or significant for multi-letter words

# 2) Overlay QA image
python3 "$SKILL/scripts/overlay_preview.py" \
  --poly project/trace/name/poly.json \
  --out project/trace/name/overlay.png

# 3) After overlay OK → SCAD + note
python3 "$SKILL/scripts/scad_from_poly.py" \
  --poly project/trace/name/poly.json \
  --out project/src/name.scad \
  --name name

# 4) Docker STL (openscad 2021.01)
docker run --rm -v "$PROJECT:/work" -w /work openscad/openscad:2021.01 \
  openscad -o /work/stl/name.stl --export-format=binstl /work/src/name.scad
```

Pure Python 3 + Pillow (no numpy required).

## Project layout

```
~/Documents/the-grid/<part>/
  docs/DESIGN.md          # envelope + hole_policy + source
  source/                 # raw gen or user images
  trace/<shape>/          # binary, poly.json, svg, overlay.png
  src/*.scad
  stl/*.stl
  renders/
  compare/                # optional CAD vs image contact sheet
```

## Compare mode

When dogfooding against CAD sculpt: same plate envelope, side-by-side overlay + STL top previews, one zip. CAD path stays control; image path is treatment.

## Common pitfalls

1. Extruding before overlay QA  
2. Tracing shaded/line-art without binarize clean  
3. px→mm after the fact (lock plate before trace)  
4. Internal holes under `filled` policy left as islands  
5. Copyright traces of franchise characters  
6. Hair-thin horns/legs under min_feature at target mm  
7. Merging this skill into openscad-printables  

## Verification checklist

- [ ] DESIGN.md: plate, frame, thickness, hole_policy, view  
- [ ] Source image under prompt contract or user PNG  
- [ ] poly.json exists; single outer ring if filled  
- [ ] overlay.png reviewed and accepted  
- [ ] STL exported; dfm_gate PASS (or documented override)  
- [ ] components=1 for filled toddler stencils  
- [ ] Zip delivered (not raw STL on Discord)  

## Done when

Recognizable silhouette at toddler glance + gated STL in plate envelope. Icon literacy beats primitive-CAD cleverness.
