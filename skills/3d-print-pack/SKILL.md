---
name: 3d-print-pack
description: Zip a gated project into a deliverable pack.
version: 1.0.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [3d-print, fdm, zip, pack, gated, deliverable, manifest]
    related_skills: [3d-print-design-brief, 3d-print-validate]
---

# 3D Print Pack

Zip a project that already passes `validate_project.py`. Not a slicer project unless `3d-print-slice` ran.

This skill is not in `/3d-print`.

## When to Use

- User says zip this gated project
- Class skills that already demand a zip (silhouette, display-enclosure)
- Delivery after HARD=0

**Don’t:** pack an ungated tree; start a print; talk to a printer.

## Procedure

```bash
python3 skills/3d-print-pack/scripts/pack_project.py "$PROJECT"
```

Refuses if `validate_project.py` would HARD-fail (calls it). Writes `pack/<part>.zip` with project-relative members only:

- `docs/PRINT_SPEC.yaml`
- `cad.source_files`
- every `geometry.stl_files[]`
- `step/` if present
- `renders/` stills if present
- generated `docs/PRINT_NOTES.md` (orientation, bed face, supports, material, nozzle, layer height — from the spec only)
- `MANIFEST.sha256`

pblend’s zip stays; this is the backend-neutral pack.

## Pitfalls

1. Packing before `validate_project.py` HARD=0
2. Absolute paths in the zip
3. Inventing print notes the spec does not state
4. Treating the zip as a sliced 3MF

## Verification

- [ ] `validate_project.py` HARD=0
- [ ] zip contains spec, source, STLs, PRINT_NOTES, manifest
- [ ] member names are project-relative
- [ ] SHA-256 manifest matches member bytes
