---
name: 3d-print-cad-render
description: Render STEP in the Rage CAD inspector.
version: 0.2.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [3d-print, cad, step, viewer, inspector]
    related_skills: [3d-print-design-brief, 3d-print-validate, 3d-print-vibecad]
---

# 3D Print CAD Render

Loopback web view of a mill STEP: OCC face tessellation plus BREP edges. Rage atlas chrome (paper `#e8e4da`, ink `#1c1b18`, one red `#c42b23`, charcoal bar `#171714`). Not a trimesh STL preview, not a mill backend, and not print approval.

This pack does not ship FreeCAD. A STEP dump needs a host `FreeCADCmd` via `FREECAD_CMD` or `VIBECAD_CMD`. Packing an existing scene JSON does not. Do not bake a home-directory binary path into this repo.

## When to Use

- render a STEP in the web inspector
- several STEP studies in one viewer (parts tree)
- after a mill, before a still

**Don't:** bind `0.0.0.0`, treat an STL as CAD, pack every model into one HTML, or commit a private hub URL, Tailscale hostname, or home path.

## How to Run

```bash
export QT_QPA_PLATFORM=offscreen
export FREECAD_CMD=/path/to/FreeCADCmd
python3 scripts/render_cad_project.py --project "$PROJECT" --serve --port 8107
```

Loopback only: `http://127.0.0.1:8107/?view=solid`.

Optional Tailscale proxy. It reads `tailscale ip -4` and exits if that is not a `100.x` address. Never hardcode an address. Never `0.0.0.0`.

```bash
python3 scripts/ts_proxy_cad.py --port 8107
```

Skip the binary when you already have an OCC dump:

```bash
python3 scripts/render_cad_project.py --scene scene.json --out-dir "$PROJECT/renders/cad-inspector"
```

`FreeCADCmd -c` never sets `__name__ == "__main__"` — dump ends with `raise SystemExit(main())`.

## Inspector

Orthographic Z-up. Parts tree when `catalog.json` is present (`path` is `folder/file`, `?model=<id>`). Installed / solid / translucent / exploded. Measure two face clicks (world mm + delta). CAD edges on by default. Section plane leaves cuts open. Assembly XYZ from the loaded mesh. Copy link keeps the model query. No directory listing.

## Procedure

1. Resolve STEP (`--step`, `step/`, or PRINT_SPEC step entries). No STEP → stop.
2. Dump inside FreeCADCmd. Scene must include faces and BREP edges.
3. Pack `viewer.html`. Do not commit multi-MB `scene.json`.
4. Serve loopback only. Verify GET 200 on `/` and `/viewer.html`.
5. Multi-model: `--catalog <dir> --model-id <id>` registers `models/<id>.json` and writes a shell. Id is `^[a-z0-9][a-z0-9-]{0,63}$`. `path` is `folder/file` (same charset, no `..`). Do not embed every STEP into one HTML.

## Pitfalls

1. STL / trimesh as the CAD view.
2. Triangle `EdgesGeometry` instead of OCC edge discretization.
3. Binding `0.0.0.0` or baking a Tailscale hostname into the repo.
4. Host `python3` dump — no FreeCAD.
5. Treating the inspector as a STEP editor or print approval.
6. Packing every model into one `viewer.html`. A bad id (`../`, uppercase) is a hard fail.
7. A default path under a home directory. Set `FREECAD_CMD`.

## Verification

- [ ] STEP dump has `edges` and tessellated faces
- [ ] `viewer.html` contains packed geometry or a catalog shell
- [ ] `curl -fsS http://127.0.0.1:<port>/viewer.html` is 200
- [ ] Server is `127.0.0.1`, not `0.0.0.0`
- [ ] pytest `tests/`
