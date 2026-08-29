# STEP kernels

OpenSCAD and Blender cannot emit editable STEP. Do not export STEP from them. Do not use `csg2stp`. Do not use Assimp-from-mesh STEP.

Product kernel: **10-X-eng/vibecad** (OCC FreeCAD fork, LGPL-2.1). Not the PyPI package `vibecad`. Printables only spawns it. Do not vendor it into this MIT repo.

CadQuery Docker is the CI STEP path when VibeCAD is absent.

## Detection

1. `--kernel vibecad` or `auto` + `VIBECAD_CMD` (x86_64 AppImage / `freecadcmd` / `VibeCADCmd`)
2. `--kernel cadquery` or `auto` + `PREVERSE_STEP_IMAGE`
3. `PREVERSE_PYTHON` venv escape hatch
4. Else exit **2**. Never write a fake STEP.

## Pins

`PREVERSE_STEP_IMAGE` must be a **digest**, not `:latest`. Local `cadquery/cadquery:latest` is CadQuery 2.1 / Python 3.8 and is forbidden.

Documented extra-extra image (override with `PREVERSE_STEP_IMAGE`):

```text
ghcr.io/cadquery/cadquery-docker@sha256:779a5be732d838eb5ed41c2f44a76f3e64fd83b91471241914d762cee3c65be8
```

Spawn:

```bash
docker run --rm -v "$PROJECT:/work" -w /work "$PREVERSE_STEP_IMAGE" python /work/src/<body>.py
```

VibeCAD:

```bash
export VIBECAD_CMD=/path/to/freecadcmd   # or the x86_64 AppImage console binary
"$VIBECAD_CMD" src/<body>.py
```

`POST /v1/run` is allowed. Never commit the token. Do not enable VibeCAD MCP (it kills the in-app Assistant).

Linux ARM qemu-x86_64 AppImage is **unsupported**. Do not treat qemu as a kernel.

Host Python must not `import cadquery` or `FreeCAD` at CLI import time. Default unit CI does not invoke VibeCAD, CadQuery, Docker, or OCC.

Native reverse runtime in VibeCAD only accepts `mesh.rebuild` and `mesh.approximate`. Parametric reconstruction is a separate modeling task (`mesh.reconstruct_parametric` upstream; [PR #131](https://github.com/10-X-eng/vibecad/pull/131)). Do not overload `mesh.to_shape`.
