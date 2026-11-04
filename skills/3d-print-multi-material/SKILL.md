---
name: 3d-print-multi-material
description: Design optional AMS colors and material regions.
version: 0.1.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [3d-print, fdm, ams, multi-material, multicolor, inlay, support-interface]
    related_skills: [3d-print-design-brief, 3d-print-vibecad, 3d-print-openscad, 3d-print-blender, 3d-print-validate, 3d-print-slice, 3d-print-pack]
---

# Optional multi-material design

Use when a part benefits from contrasting labels, inlays, dedicated support
interfaces, or multiple functional materials, or the user requests them.
Single-material remains the default. Having an AMS does not require a second
filament or an extra question on every design.

## Choose the manufacturing strategy

- **Color:** prefer the same polymer for readable markings or an intentional
  palette. Place markings on a small number of layers when that serves the
  design; repeated changes through the full height can dominate time and waste.
- **Support-interface:** keep the support base in the model material and use a
  dedicated filament only at the contact interface. Preserve access to remove
  supports. A soluble interface does not make an enclosed support base removable.
- **Functional:** verify the actual pair's temperature requirements, adhesion,
  service environment and joint geometry. Consider a mechanical interlock or
  separately printed insert. Require an actual measured/fit-tested bond report
  for the joined design; never invent a coupon result or claim strength from CAD.

Record the benefit in `multi_material.reason`. Omit the entire block when one
material is appropriate. A different color is still a separate logical filament,
even when its polymer and slicer preset match another entry.

Read [the contract](references/material-contract.md) when writing `PRINT_SPEC`.
Read [P1S / AMS 2 Pro capabilities](references/p1s-ams-2-pro.md) for this setup;
feed compatibility, co-printing compatibility and bonding are separate checks.

## Preserve one printed object

Keep the existing one-composite-STL-per-printed-body contract. For an inlay or
another material domain, export additional closed region STLs in the **same CAD
coordinate frame**. Regions partition the composite; touching boundaries are
legal, overlapping interiors or missing occupancy are not. Export each region
with its own shell count and material id. A region is not a separate component
to move to the bed, rotate, or pack independently. Do not union away its identity.

Run `3d-print-validate` after export. It audits both the composite and the regions,
compares volumes, and samples interior coverage. This is not an exact CAD boolean
proof; check the source kernel's partition and the actual slicer result too.

## Plan, export and deliver

After geometry validation, `3d-print-slice` writes the material plan, process card
and native Studio assemble list:

```bash
python3 skills/3d-print-slice/scripts/slice_project.py "$PROJECT"
```

With explicit installed machine/process/filament presets and a configured
`BAMBU_STUDIO`, it can export a real multi-material project. See
`3d-print-slice` for the arguments. One logical material id maps to one project
filament. Physical AMS slots are mapped from the actual loaded spools at job
setup, not permanently encoded into CAD.

The native export checker rejects empty 3MFs, lost body groups, changed region
geometry, wrong filament colors/assignments and missing support-interface
settings. Geometry fingerprints use 0.001 mm quantization. Estimates stay
unavailable until a real slice provides them. Do not substitute guessed times,
purge values or a renamed STL. Do not flush incompatible support filament into
functional model infill.

For a Studio review, use its existing unsliced workflow with the generated
assemble list and all filament presets; skip independent STL packing. Keep the
material-aware export/check in this package as the authoritative handoff.
`3d-print-pack` includes regions, material notes and generated material artifacts.
Printer upload/start remains in the configured printer-control tools and the
user's authorization; this skill never starts a printer or a drying cycle.

## Calibration before a functional claim

Print the actual material pair with the intended layer height, orientation,
joint and transition/purge settings. Record the specimen, filament identities,
settings, test method, observed failure and acceptance criterion in the named
report. An interface-removal trial checks surface and removability; a joined
material trial checks the joint under its intended load. A generic cube or dry
AMS air reading cannot establish either result.

The public examples are software specimens with invented dimensions. They do not
claim a tested physical bond or production fit.
