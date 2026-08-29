---
name: 3d-print-vibecad
description: Remake a PRINT_SPEC part in VibeCAD.
version: 1.0.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [3d-print, fdm, vibecad, vibescript, remake]
    related_skills: [3d-print-design-brief, 3d-print-validate, 3d-print-openscad]
---

# 3D Print VibeCAD

Optional remake path for a validated `docs/PRINT_SPEC.yaml` inside **10-X-eng/vibecad** (FreeCAD fork, VibeScript/Native, in-app Grok Assistant). Not the PyPI package named vibecad. Not the default CAD kernel.

Point the in-app Assistant at `references/vibecad-host.md`.

## When to Use

Use when the human is already in VibeCAD, or explicitly asks to remake a PRINT_SPEC part in VibeCAD.

Do not use for a new dimensional bracket; that is `3d-print-openscad`. If VibeCAD is down, stay on OpenSCAD. Do not enable VibeCAD MCP.

## Hard sequence

1. `3d-print-design-brief` — write and validate `docs/PRINT_SPEC.yaml` first. `cad.backend: vibecad`, `cad.parametric: true`. Chat, `.FCStd`, MJCF, and `DESIGN.md` cannot override it.
2. VibeScript / Part CSG with named millimetre parameters (`identifier =`) for every PRINT_SPEC dimension. Source is project-relative `.py` or `.vibescript`, not Markdown-only, not `.FCStd`-only.
3. Export a **binary STL** inside VibeCAD (one STL per independently manufactured body).
4. `3d-print-validate/scripts/validate_project.py` on the project. If `assembly` is present, also `validate_assembly.py`. HARD fail means not done.

A VibeCAD preview is not printable. Host `python3` has no FreeCAD; geometry scripts execute inside VibeCADCmd/freecadcmd or `POST /v1/run`.

## Geometry law

Booleans must produce the declared `expected_shells`. `fuse` / `multiFuse` of overlapping solids that remain N shells is HARD, not a preview pass. Do not waive shell-count because OCC tessellation is noisy. Short STL chords stay warning-only.

`overlapping_solids_allowed` stays false. Assumed critical fits cannot ship. `hybrid` still means separate bodies, not two kernels editing one body.

## Control surface

Three different channels — do not mix them up:

| Channel | What it is |
|---|---|
| In-app Assistant (Grok) | Human signs in under VibeCAD Preferences. Point it at `references/vibecad-host.md`. |
| Agent HTTP | Optional loopback `127.0.0.1:8766` with `Authorization: Bearer` from `~/.local/share/VibeCAD/agent/token`, or `POST /v1/run`. |
| MCP | `127.0.0.1:8765/mcp` disables the in-app Assistant. **Do not enable VibeCAD MCP.** |

Never commit the token. The agent must never type passwords or device codes; sign-in stays in VibeCAD Preferences.

## Install / detect (10-X-eng AppImage)

This pack does not vendor VibeCAD. Detect the upstream binary, then spawn it.

```bash
python3 scripts/find_vibecad.py status
# optional: fetch latest x86_64 AppImage to ~/.local/opt/vibecad/
python3 scripts/find_vibecad.py download
export VIBECAD_CMD=...   # printed by status/download
```

Download only on x86_64. Linux ARM qemu-x86_64 AppImage is not a supported backend. Do not enable VibeCAD MCP. `status --probe-http` may GET `127.0.0.1:8766/v1/status`; it never prints the token.

Manual: [10-X-eng/vibecad releases](https://github.com/10-X-eng/vibecad/releases/latest), `chmod +x VibeCAD*.AppImage`, export `VIBECAD_CMD`.

```bash
# x86_64 AppImage / freecadcmd only. Linux ARM qemu-x86_64 AppImage is not a supported backend.
export VIBECAD_CMD=/path/to/freecadcmd   # or the x86_64 AppImage console binary
"$VIBECAD_CMD" src/<part>.py
```

```bash
# GUI already running: loopback Bearer, never commit the token file
TOKEN=$(cat ~/.local/share/VibeCAD/agent/token)
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"script":"src/<part>.py"}' \
  http://127.0.0.1:8766/v1/run
```

Then:

```bash
python3 3d-print-validate/scripts/validate_project.py "$PROJECT"
```

## Pitfalls

- Treating a VibeCAD preview or `.FCStd` as the contract
- `multiFuse` that still exports N shells while `expected_shells` is 1
- Running the geometry script with host python3
- Enabling MCP and losing the in-app Assistant
- Using Linux ARM qemu-x86_64 AppImage
- Making VibeCAD the default for a new bracket

## Verification

- [ ] print spec passes with `cad.backend: vibecad` and Python/VibeScript sources
- [ ] every PRINT_SPEC dimension has `identifier =` in source
- [ ] binary STL exported inside VibeCAD
- [ ] `validate_project.py` reports HARD=0
- [ ] `validate_assembly.py` if assembly is present
