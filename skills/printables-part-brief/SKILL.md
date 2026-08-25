---
name: printables-part-brief
description: "Use before OpenSCAD when starting or redesigning a 3D-printable part from text or images. Writes docs/DESIGN.md with product class, orientation, intended components, fit provenance, wet-service requirements, dimensions, and never-list. Pair through /printables."
license: MIT
metadata:
  version: "1.1.0"
  author: Tron
  platforms: linux
  hermes:
    tags: [3d-print, intent, design-brief, image, vision, dfm, printables, bambu]
    related_skills: [openscad-printables, printables-dfm-gate, define-goal]
---

# Printables Part Brief — intent before CAD

## Overview

Lock **what** to make and **how it prints** before writing a single line of OpenSCAD. Optional reference images become structured findings (measured vs assumed), not freehand invent-dims.

This skill is step 1 of the manufacturing loop. CAD = `openscad-printables`. Gates = `printables-dfm-gate`. Prefer the `/printables` bundle so all three load together.

## When to Use

- New stand / mount / bracket / enclosure / hinge / sled
- “Print this”, “model this”, redesign for FDM
- User attaches a photo of hardware, sketch, or aesthetic reference
- Before any `.scad` on a `/printables` job

**Don’t use alone for pure software tasks.** Don’t skip this and jump to CAD.

## Workflow

1. **Collect inputs**
   - Text description (required)
   - Optional image path(s) from Discord/gateway/`cache/images/`/local file
   - Known dims Marc states (treat as measured)

2. **If image present → vision first**
   - Use `vision_analyze` on the image path (Hermes redirects raw image reads there)
   - Follow `references/image-context-protocol.md`
   - Record findings under `## Reference image` in DESIGN.md
   - Mark each dimension **measured** | **assumed** | **from-user**
   - Never invent ±0.1 mm fits from a single photo

3. **Classify product class** (pick one)

   | Class | When |
   |-------|------|
   | `equipment-open-frame` | Elevated base for bottom-vent gear (DGX-class) |
   | `tray` | Soft tray / midspan fill intentional |
   | `bracket` | L-bracket, sensor mount, clamp |
   | `wet-fixture` | Drainable water guide, faucet aid, soap/wet accessory |
   | `enclosure` | Box / lid / case |
   | `pip-hinge` | Print-in-place hinge/lid mechanism |
   | `generative` | Load-path / organic (not pin stilts under gear) |
   | `other` | Must justify in DESIGN.md |

4. **Write intent card** to `docs/DESIGN.md` using `references/intent-card-template.md`

   Required keys (YAML frontmatter or clearly labeled lines — gates parse both):

   ```
   product_class: equipment-open-frame
   print_orientation: TOP-FIRST
   print_up_axis: Z
   use_flip: yes
   soft_mode: yes|no
   stack_story: none
   clearance_mm: 0.8
   expected_components: 1
   fit_required: yes|no
   critical_fit_status: measured|from-user|fit-tested|assumed|none
   service_environment: dry|wet
   drainage: none|open-continuous|through-drain|drainable
   ```

5. **Never-list** (always include defaults + case-specific)

   Defaults for FDM / Marc taste:
   - pin forest under seating deck
   - mid-air X-braces
   - posts/tabs inside chassis XY (equipment/stack)
   - CAD before orientation lock
   - raw cube soft-mode exteriors when soft requested

6. **Mode: Explore vs Converge**
   - Explore: ≤5 form variants then **forced pick** — do not polish all five
   - Converge: change budget 1–3 goals only

## Completion criteria

Done when all true:

- [ ] `docs/DESIGN.md` exists under the project dir (`~/Documents/the-grid/<part>/`)
- [ ] `product_class` + `print_orientation` locked
- [ ] Critical dims listed with measured/assumed/from-user/fit-tested tags
- [ ] Precision mating interfaces declare `fit_required` + `critical_fit_status`
- [ ] `expected_components` states the intended STL shell count
- [ ] Wet-service parts declare drainage, material, retention, and cleaning access
- [ ] Never-list present
- [ ] If image: Reference image section with `image_role: metrology|style|context`
- [ ] Scaffold choice named (which template the CAD skill must start from)

**Do not write `.scad` in this skill.** Hand off to `openscad-printables`.

## Scaffold map (for handoff)

| product_class | Start template |
|---------------|----------------|
| equipment-open-frame | `open_frame_equipment_scaffold.scad` |
| tray | `soft_part_scaffold.scad` |
| bracket / wet-fixture / enclosure / other | `part_scaffold.scad` or soft helpers |
| pip-hinge | `pip_hinge_cones.scad` |
| generative | `generative_loadpath.scad` (not under equipment seating) |
| blender-bpy (scaffold key) | Lid/organic half only — hand off **`blender-printables`** / `pblend`. Prefer **hybrid** for full cases: OpenSCAD base + Blender lid. Set `scaffold: blender-bpy` on the lattice half; note `backend: hybrid` in DESIGN. |
| hybrid (full case) | OpenSCAD base/tray + Blender or OpenSCAD lattice lid. Gold: `rpi-zero-print-noloop`. |

## Common pitfalls

1. Jumping to SCAD “just to explore form” before intent  
2. Treating a phone photo as a caliper  
3. Leaving stack story ambiguous (tower vs sled thrash)  
4. Forgetting print orientation / use flip  
5. Classifying DGX-class gear as `tray` (leads to waffle/pins under deck)  
6. Calling an assumed photo dimension a production fit  
7. Omitting intended shell count, wet drainage, or mechanical retention  
8. Exploring five silhouettes then shipping all five  

## Verification checklist

- [ ] DESIGN.md intent complete  
- [ ] Image protocol followed if media attached  
- [ ] Product class matches scaffold map  
- [ ] Never-list includes open-frame rejects when equipment  
- [ ] Explicit “ready for CAD” note at end of DESIGN.md  
