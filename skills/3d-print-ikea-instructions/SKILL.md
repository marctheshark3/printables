---
name: 3d-print-ikea-instructions
description: Build required-sequence assembly sheets from a mill STEP.
version: 0.1.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [ikea, sequence, booklet]
    related_skills: [3d-print-lego-instructions, 3d-print-cad-render]
---

# IKEA-style assembly sheets

Required-sequence sheets from a mill STEP: one new solid per step, exploded off the parts already placed, with a ghost of where it sits. Not an IKEA manual, not a fastener plan, and not print approval.

Stdlib Python only. It does not call the inspector. The toolbar button `instructions` is the picture path in `3d-print-lego-instructions`. A named style from the user wins over the heuristic below.

## When to Use

- "IKEA instructions" / "one way only" / "required sequence" / "if you skip a step it will not close"
- the final result depends on one sequence (orientation, panels that fit one way, hardware order)

**Picture path instead** (`3d-print-lego-instructions`) when the picture matters more than a single legal order. Construction blueprints. Kits. Identical copies added together. "What it looks like so far."

**Named preference wins.** If the user says Lego, IKEA, blueprint, or one way only, use that style even when the heuristic disagrees.

**Don't:** invent screws, cams, dowels, or article numbers. Don't use this for a picture-first blueprint.

## Prerequisites

- An OCC dump (`source` is `occ-step` or `occ-brep`) with `vertices` and BREP `edges`, or stop
- Host `python3` (stdlib only)
- Optional `--order`: comma-separated instance names, each dump part once

## How to Run

From the pack root, invoke through the `terminal` tool:

```bash
python3 skills/3d-print-ikea-instructions/scripts/render_ikea_booklet.py \
  scene.json --out ikea.html --title "Assembly"
python3 skills/3d-print-ikea-instructions/scripts/render_ikea_booklet.py \
  scene.json --out ikea.html --order "base,side-a,side-b"
python3 skills/3d-print-ikea-instructions/scripts/render_ikea_booklet.py --self-check
```

Picture sheets are the other skill:

```bash
python3 skills/3d-print-lego-instructions/scripts/render_booklet.py \
  scene.json --out instructions.html --title "Assembly"
```

## Quick Reference

- User names a style → that style
- Picture over order (blueprint, kit, stack) → `3d-print-lego-instructions`
- One legal sequence to get the final result → this skill
- Unsure → ask. Do not guess a fastener plan
- One solid per step. No 2 mm fingerprint batch
- Default order: `centroid z, then y, then x, then name`
- Note: `This sequence is required. Not an IKEA manual. Not print approval.`
- New part: solid black, offset in +X. Installed seat: dashed ghost. Arrow between them
- Button `instructions` batches copies and shades the build so far. That is not this booklet

## Procedure

1. Read the user's words for a style. Completion: picture path, this skill, or ask. A named preference is not overridden.
2. If they did not name one: picture path when order is not the product (blueprints, visual build-so-far). This skill when the piece must go together one way or the result is wrong. Both true, or only centroids and no stated sequence → ask before printing this booklet as required.
3. Picture path: stop and follow `3d-print-lego-instructions`. Completion: no `ikea.html`.
4. This skill: resolve an OCC dump. No dump → stop. An STL mesh source is a hard fail (`dump.source must be occ-step`).
5. If the user gave the sequence, pass `--order`. Completion: the script accepts it, or exits 1 because a name is missing or repeated.
6. Write `ikea.html`. Completion: a parts sheet, then one `data-step` per solid, the required-sequence note, and no screw or cam markup.
7. Print to PDF from the browser. This pack does not ship a PDF compiler.
8. Do not treat the sheet as print approval. That gate is `3d-print-validate`.

## Pitfalls

1. Centroid order is a deterministic reading order. It is not a detected mate, fastener, or removal plan. Do not draw hardware the dump does not contain.
2. This booklet presents one sequence as required. It does not prove no other order works.
3. The picture planner groups identical fingerprints inside a 2 mm band. That batch is wrong here. This script does not take `--z-band-mm`.
4. The inspector Instructions button is the picture path. Do not call that overlay an IKEA booklet.
5. Exploded +X is a drawing offset, not the build direction.
6. One solid is one page. Do not invent sub-steps inside a solid.
7. Sheet box is `box-sizing: border-box` and `min-height: 273mm` under `@page { size: A4; margin: 12mm; }`. A content-box min-height plus padding spills the page.

## Verification

- [ ] `python3 skills/3d-print-ikea-instructions/scripts/render_ikea_booklet.py --self-check` exits 0
- [ ] `ikea.html` contains `This sequence is required` and one `data-step` per solid
- [ ] Two identical boxes are two steps, not one `2×` callout
- [ ] The diff has no home path and no Tailscale hostname
