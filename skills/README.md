# Skill catalog

Choose a skill by the job you need. Every skill uses the same `PRINT_SPEC.yaml` contract and shared validation rules. See [getting started](../docs/getting-started.md) for installation and [the guides](../docs/README.md) for commands.

## Core workflow

These five skills are loaded by the [`/3d-print` bundle](../skill-bundles/3d-print.yaml).

| Skill | Job |
|---|---|
| [3d-print-design-brief](3d-print-design-brief/SKILL.md) | Define dimensions, tolerances, provenance, and the manufacturing contract. |
| [3d-print-vibecad](3d-print-vibecad/SKILL.md) | Build dimensional mechanical CAD with 10-X-eng/vibecad. |
| [3d-print-openscad](3d-print-openscad/SKILL.md) | Export CI samples, handle requests naming OpenSCAD, or work when VibeCAD cannot run. |
| [3d-print-blender](3d-print-blender/SKILL.md) | Build organic or lattice geometry. |
| [3d-print-validate](3d-print-validate/SKILL.md) | Check the contract, exported STLs, and assemblies. |

## Parts and input methods

| Skill | Job |
|---|---|
| [3d-print-display-enclosure](3d-print-display-enclosure/SKILL.md) | Design a small two-piece display enclosure. |
| [3d-print-robotics](3d-print-robotics/SKILL.md) | Design the numbered 01 FDM rover family around bought hardware. |
| [3d-print-shop-fixture](3d-print-shop-fixture/SKILL.md) | Decide whether to print or buy a shop fixture. |
| [3d-print-image-silhouette](3d-print-image-silhouette/SKILL.md) | Turn an image outline into a stencil or silhouette. |
| [3d-print-photo-cad](3d-print-photo-cad/SKILL.md) | Recover a ChArUco board's scale from a photo; part dimensions still need evidence. |
| [3d-print-reverse](3d-print-reverse/SKILL.md) | Rebuild an STL as editable STEP and a validated STL. |

## Review and instructions

| Skill | Job |
|---|---|
| [3d-print-cad-render](3d-print-cad-render/SKILL.md) | Inspect STEP geometry, parts, faces, edges, and dimensions in the loopback viewer. |
| [3d-print-sim](3d-print-sim/SKILL.md) | Check assembled occupancy, joint sweeps, and load sections. |
| [3d-print-lego-instructions](3d-print-lego-instructions/SKILL.md) | Make picture-led assembly sheets, including the inspector's Instructions view. |
| [3d-print-ikea-instructions](3d-print-ikea-instructions/SKILL.md) | Make a required-sequence booklet with one solid per step. |

## Delivery

| Skill | Job |
|---|---|
| [3d-print-pack](3d-print-pack/SKILL.md) | Zip a validated project with source, STLs, print notes, and a checksum manifest. |
| [3d-print-slice](3d-print-slice/SKILL.md) | Write process cards and, when a slicer is configured, 3MF files. |

## Installation and layout

`./install.sh` copies all cataloged skills except `3d-print-cad-render`, so a profile-local inspector is not overwritten. Skills outside the core workflow are available separately and are not loaded by `/3d-print`. Live printer control is maintained in the sibling `bambu-mcp` repository.

Skill directories stay flat under `skills/` because the installer and scripts resolve sibling skills by name. Each package owns its `SKILL.md` and any scripts, tests, templates, or references it needs. Shared walkthroughs live in [`docs/guides/`](../docs/README.md#guides).

[Back to Printables](../README.md)
