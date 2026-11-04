---
name: 3d-print-slice
description: Emit a slicer process card and optional 3MF.
version: 1.1.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [3d-print, fdm, slice, slicer, 3mf, process-card]
    related_skills: [3d-print-design-brief, 3d-print-validate, 3d-print-multi-material]
---

# 3D Print Slice

Read `print:` and `manufacturing:` from `docs/PRINT_SPEC.yaml` and write a process card. Optionally emit a 3MF when a slicer CLI is on PATH via env. This skill does not talk to a printer.

This skill is not in `/3d-print`.

## When to Use

- User says slice this PRINT_SPEC
- A gated STL needs a process card before a human or bambu-mcp print
- Envelope HARD repair via split-for-bed (explicit; never silent scale)

**Don’t:** start a print; require a slicer in CI; rename an STL to `.3mf`.

## Procedure

```bash
python3 skills/3d-print-slice/scripts/slice_project.py "$PROJECT"
```

Always writes `slice/<body>.process.json` with printer profile name, build volume, nozzle, layer height, material, bed face, up axis, supports policy, max overhang, and the per-body STL path.

If `ORCA_SLICER` / `BAMBU_STUDIO` / `PRUSA_SLICER` is set and executable, also write `slice/<body>.3mf`. If not, skip 3MF and print `SKIP: no slicer CLI`. Never write an empty or STL-renamed “3MF”.

Split an envelope overflow (explicit, two bodies):

```bash
python3 skills/3d-print-slice/scripts/split_for_bed.py \
  --length-mm 300 --envelope-mm 256 256 256 \
  --clearance-per-side-mm 0.2 --out "$PROJECT/split"
```

Do not silently scale the part down.

## Afterward

If bambu-mcp is configured in the agent MCP list and BAMBU_* env is set,
the agent may upload slice/<body>.3mf. A validated STL is not permission
to print. user confirmation stays in bambu-mcp (write tools).

Missing bambu-mcp or missing env → skip, exit 0 on the printables side.

## Pitfalls

1. Fake 3MF
2. Printer IP / access code in PRINT_SPEC
3. Starting a print because validate HARD=0
4. Automatic split

## Verification

- [ ] process card JSON matches spec `print:` / `manufacturing:`
- [ ] no `.3mf` when slicer env is unset
- [ ] stdout contains `SKIP: no slicer CLI` without a slicer
- [ ] split of a 300 mm bar yields two bodies inside 256³

## Optional multi-material Studio path

When `multi_material` is present, validate all geometry first and emit
`slice/project.process.json`, `slice/material-plan.json`, and the native
`slice/assemble-list.json`. One plate contains each independently printed body;
its material regions stay aligned as native parts of that object. No profiles
means a usable material plan and an explicit skip, with no invented 3MF or
estimates. Regeneration removes this path's older exports to prevent stale files.

Provide the installed presets for an actual export (paths are examples):

```bash
BAMBU_STUDIO=/path/to/bambu-studio python3 skills/3d-print-slice/scripts/slice_project.py "$PROJECT" \
  --machine /profiles/machine.json --process /profiles/process.json \
  --filament shell=/profiles/pla.json --filament mark=/profiles/pla.json \
  --plate-type 'Textured PEI Plate'
```

Use logical material ids from the spec, not physical AMS slot numbers. Filament
preset names must match the spec. Inherited installed presets are resolved into
temporary files; `--profile-root` selects their vendor profile tree when it
cannot be inferred. Do not commit copied system presets. The adapter verifies
the printer/nozzle, applies the declared shared bed temperature, and checks the
export's bodies, region geometry, colors and filament assignments. Other slicer
environment variables do not enable this Studio-specific path.

The default export is an unsliced `slice/project.3mf`. Add `--slice` only for an
explicit request to slice; that produces `slice/project.gcode.3mf`. This still
does not upload or start a print. Estimates are taken from real slice metadata
when present; unavailable fields remain null. Do not infer costs from a render.
