# Goal: reverse-engineer STL → editable STEP → gated STL

**Status:** ready to implement.
**Handoff:** execute this file as the full brief. Do not rediscover the method.
**Method:** [STL to STEP — the proper way](https://www.youtube.com/watch?v=wEN89D1w4JA&t=61s) (Kanrog Creations). Reconstruction from a reference mesh, not triangle conversion.
**Product kernel:** [10-X-eng/vibecad](https://github.com/10-X-eng/vibecad) (OCC FreeCAD fork, LGPL-2.1). Not the PyPI package `vibecad`.
**This repo:** Printables. Follow `CONTRIBUTING.md`. Do not invent a second manufacturing contract.

Paste for the next agent:

> Execute `docs/GOAL-stl-to-step.md`. Build skill `3d-print-reverse` and CLI `preverse` in this pack. Reconstruction, not conversion. Triangle-wrapped STEP is HARD. Product kernel is 10-X-eng/vibecad (fork/PR there, do not vendor LGPL here). CadQuery Docker is the CI STEP path when VibeCAD is absent. Unit CI stays free of OCC. Start at analyze/segment tests, not STEP export.

---

## Job

Printables already does new parts: `PRINT_SPEC.yaml` → CAD → one STL → `validate_project.py`. Add the missing entry: **an existing STL in, an editable B-rep STEP plus a gated STL out.**

The video’s process, in order:

1. Import the STL as **reference only**. Do not convert it.
2. Align to world, millimetres.
3. Measure (axis-aligned lengths, radii, chamfers).
4. Sketch on real planes; project mesh vertices as construction.
5. Rebuild with extrude / revolve / loft / boolean / hole / fillet / chamfer / mirror.
6. Export analytic STEP (planes, cylinders, cones, spheres, fillets — not one face per triangle).
7. Compare rebuilt solid vs input mesh. Deviation is the proof.

There is no automatic converter that produces a proper CAD file. Recreate the part. The result must be faces you can select and parameters you can change.

---

## Done means

A run is finished only when **all** of these hold:

1. `docs/PRINT_SPEC.yaml` passes `validate_print_spec.py`.
2. Parametric CAD source exists (named millimetre parameters; no unexplained literals).
3. `step/<body>.step` is analytic B-rep, not tessellated faces.
4. `stl/<body>.stl` comes from that B-rep (or the same IR) and `validate_project.py` is HARD=0.
5. `reports/<body>.deviation.json` two-sided max deviation vs the **input** STL ≤ `max_deviation_mm`.
6. Same input bytes + flags → same IR/reports (sorted JSON) and geometry within float eps.
7. Changing a named parameter regenerates STEP + STL.

**Triangle-wrapped STEP is HARD.** If face count ≥ 0.9 × input triangles, refuse to write `step/` and exit non-zero.

### Classify every STL. Never invent CAD.

| Class | When | What you ship |
|---|---|---|
| `parametric` | Feature IR rebuilds within `max_deviation_mm` | IR + PRINT_SPEC + CAD source + STEP + STL |
| `analytic` | Planes/cylinders/cones/spheres/tori fit; no feature tree | Fitted B-rep STEP + STL + report |
| `organic` | Only if a new part would already be `cad.backend: blender` | NURBS STEP + STL + explicit flag |
| `failed` | Illegal mesh or no class meets tolerance | JSON report only. **No** STEP/STL claim |

`parametric` is the default target for brackets, mounts, enclosures. Mixed classes per region must be listed. Silent mixed output is HARD.

---

## Kernels (binding)

OpenSCAD and Blender **cannot** emit editable STEP. Do not export STEP from them. Do not use `csg2stp`.

One body, one kernel. Do not invent `cad.backend: reverse`. Reverse is a skill. The kernel is OCC.

| Track | When | How |
|---|---|---|
| **B — 10-X-eng/vibecad** | Product path. `VIBECAD_CMD` set, x86_64 AppImage / `freecadcmd` / `VibeCADCmd` | Fork/PR **that** repo. Printables only spawns it. |
| **A — CadQuery Docker** | CI / no VibeCAD binary | Pinned digest, spawn like OpenSCAD Docker. Not `:latest` (local `cadquery/cadquery:latest` is CQ 2.1 / Py 3.8). |

Detection for STEP export:

1. `--kernel vibecad` or `auto` + `VIBECAD_CMD`
2. `--kernel cadquery` or `auto` + `PREVERSE_STEP_IMAGE`
3. `PREVERSE_PYTHON` venv escape hatch
4. Else exit **2**. Never write a fake STEP.

Default unit CI does **not** invoke VibeCAD, CadQuery, Docker, or OCC. Host Python must not `import cadquery` or `FreeCAD` at CLI import time. ARM qemu-x86_64 AppImage is unsupported. VibeCAD MCP stays off (it kills the in-app Assistant). Do not vendor LGPL VibeCAD into this MIT repo.

`cad.backend` on a reverse project is `vibecad` or `cadquery`, matching the rebuild source. Never lie with `openscad`. Optional new enum value `cadquery`, same bar as `vibecad`. `/3d-print` bundle does **not** gain this skill.

### 10-X-eng/vibecad — use what exists, add the missing task

Already there (do not reimplement): `mesh.io`, `mesh.inspect` / `repair` / `segment`, Native `mesh.approximate` (plane, cylinder, sphere, polynomial, B-spline surface/curve) with `rms_deviation_mm`, C++ `SampleConsensus` (also cone/torus, not all Native yet), `RegionGrowing`, `inspect.compare`, Part Design + Sketcher VibeScript, `POST /v1/run` + `VibeCADAgentCli.py`.

`mesh.to_shape` is a **faceted** OCC snapshot. Upstream says it is not design intent. Never treat it as reverse-engineered STEP.

Native reverse runtime only accepts `mesh.rebuild` and `mesh.approximate`. Parametric reconstruction is not in that enum.

Upstream already named the gap (`docs/mesh-tool-sharpening.md`): sketches, features, and dimensions from scan geometry are a **separate modeling task**. Follow their `AGENTS.md`: additive, keep old tools, no schema breaks without owner approval.

**VibeCAD fork/PR (separate repo):**

1. New capability `mesh.reconstruct_parametric` (do not overload `mesh.to_shape`).
2. Use existing approximate / RANSAC / region grow → constrained sketches → Part Design extrude/revolve/loft/pocket/hole/fillet/chamfer/mirror.
3. Emit/consume printables `reverse/<body>.ir.json` (`schema_version: 1`). No second contract.
4. Export millimetre AP214 STEP + binary STL. Classify `parametric` / `analytic` / `failed`.
5. Optional additive `approx_cone` / `approx_torus` from existing C++ enums.
6. Boolean weld: overlapping solids must yield `expected_shells` (known pack limit).
7. Deterministic Native/VibeScript. Assistant may *call* tools. LLM is not the kernel.

**Printables, stock VibeCAD, no fork required first:** extend `examples/bracket-coupon-vibecad` so `export_if_vibecad.py` writes `step/bracket-coupon.step` via `Part.export` when `VIBECAD_CMD` is set. Coupon L-bracket must stay a handful of planes + cylinders, not triangle-count faces.

---

## Skill `3d-print-reverse`

Copy patterns from `3d-print-image-silhouette` (CLI + tests) and `pblend` (spawn CAD). Reuse `3d-print-validate/scripts/stl_io.py` and `topology.py`. Do not copy-paste parsers.

Frontmatter:

- `name: 3d-print-reverse`
- `description: Rebuild an STL as editable STEP and gated STL.` (≤60 chars, period)
- `author: Marc Mailloux, Hermes Agent`
- `license: MIT`
- `platforms: [linux]`
- tags: `3d-print`, `stl`, `step`, `reverse-engineering`, `brep`
- `related_skills`: `3d-print-design-brief`, `3d-print-validate`, `3d-print-openscad`, `3d-print-vibecad`

Wire: `install.sh` `SKILLS=`, `tests/test_skill_contract.py` `EXPECTED`, README skill list, STATUS supported path + limits, CI `py_compile` + pytest path. Do **not** add to `skill-bundles/3d-print.yaml`.

### CLI `skills/3d-print-reverse/scripts/preverse`

| Command | Job | Needs OCC? |
|---|---|---|
| `analyze` | Load STL, topology, AABB/PCA align, units | no |
| `segment` | Dihedral region grow; fit plane/cylinder/cone/sphere | no |
| `sketch` | Planar sections; 2D line/arc/circle | no |
| `features` | Hypothesis: extrude/revolve/loft/hole/fillet/chamfer/mirror/pattern | no |
| `spec` | Emit/update `docs/PRINT_SPEC.yaml` | no |
| `rebuild` | IR → kernel source (`--kernel cadquery\|vibecad\|auto`) | yes for STEP |
| `export` | Write `step/*.step` and `stl/*.stl` | yes for STEP |
| `compare` | Two-sided sampled deviation vs input STL | no for mesh/mesh |
| `gate` | `validate_print_spec` + `validate_project` + deviation HARD | no extra |
| `run` | analyze → … → gate | yes for STEP |

Agent one-liner: `preverse run --stl in.stl --project $PROJECT`

Exit: `0` success class; `1` failed/incomplete with artifacts; `2` input/schema/missing kernel. `--force` may analyze an open mesh; it must not deliver STEP/STL.

Scripts (stdlib, argparse, importable): `preverse`, `preverse_cli.py`, `mesh_analyze.py`, `segment_surfaces.py`, `extract_sketches.py`, `hypothesize_features.py`, `emit_print_spec.py`, `rebuild_cad.py`, `export_step.py`, `compare_deviation.py`.

Templates: `PRINT_SPEC.yaml.tmpl`, `reverse_ir.schema.json`, `DESIGN.md.tmpl`.

References: `reconstruction-method.md`, `reverse-ir.md`, `step-kernel.md` (CadQuery digest, VibeCADCmd, ARM qemu unsupported).

Tests under `scripts/tests/`: CLI, cube segment, cylinder plate, cube=extrude, spec validator, triangle-wrap reject, alignment stability, sorted JSON identity.

---

## IR (`<project>/reverse/<body>.ir.json`)

PRINT_SPEC stays the manufacturing contract. The IR is the only rebuild input. Markdown cannot override it. Arrays sorted by stable id. Floats fixed to 6 decimal places.

```json
{
  "schema_version": 1,
  "units": "mm",
  "input_stl": "source/original.stl",
  "body": "bracket",
  "class": "parametric",
  "alignment": {
    "method": "pca-aabb",
    "translation_mm": [0.0, 0.0, 0.0],
    "rotation_rpy_deg": [0.0, 0.0, 0.0]
  },
  "tolerance": {
    "fit_mm": 0.05,
    "max_deviation_mm": 0.2,
    "snap_mm": null
  },
  "dimensions": [
    {
      "name": "width",
      "parameter": "width_mm",
      "raw_mm": 39.97,
      "value_mm": 39.97,
      "tolerance_mm": 0.2,
      "source": "measured"
    }
  ],
  "sketches": [],
  "features": [],
  "regions": {
    "plane": 0,
    "cylinder": 0,
    "cone": 0,
    "sphere": 0,
    "torus": 0,
    "fillet": 0,
    "freeform_triangles": 0,
    "fallback": 0
  },
  "forbidden": { "triangle_wrapped_step": true }
}
```

Do not snap to “nice” numbers unless `--snap-mm` is set. Always store `raw_mm` and `value_mm`. Mesh-derived dims are `source: measured`. Assumed critical fits still cannot ship. Every IR dimension becomes a PRINT_SPEC `dimensions[]` row with the same `parameter`.

v1 features: sketch on `xy|xz|yz|offset|midplane|3-point`; extrude add/cut (blind, through-all, to-face); revolve; loft; boolean union/subtract; hole; fillet; chamfer; mirror; pattern when evidenced. No T-splines in v1.

Optional PRINT_SPEC block (keep optional so existing examples stay valid):

```yaml
reverse:
  input_stl: source/original.stl
  ir: reverse/bracket.ir.json
  class: parametric
  max_deviation_mm: 0.2
  step_files:
    - path: step/bracket.step
      body: bracket
```

If you add it, update `print_spec.py`, `print-spec-v1.md`, and tests in the same PR.

---

## Pipeline

1. **Analyze** — existing STL loader; weld `1e-5` mm; HARD if open/non-manifold unless `--force`; AABB/volume/shells; PCA then snap axes to XYZ; origin `center` default; units mm unless `--units inch` (scale 25.4 once). Never guess scale.
2. **Segment** — region-grow dihedral default 15°; fit plane → cylinder → cone → sphere; accept only if every vertex ≤ `fit_mm`; reject coverage the mesh does not have; sort by area then stable vertex-index hash.
3. **Sketch** — slab each large plane ±`fit_mm`; fit line/circle/arc; close profiles; inner loops = holes; record only observed constraints.
4. **Features** — extrude if parallel planar caps; revolve if profile + axis; hole if cylinder through plate; fillet/chamfer from blend radius; mirror if midplane evidence. If dry-run tessellation ≤ `max_deviation_mm` → `parametric`; else fitted B-rep → `analytic`; else `organic`/`failed`.
5. **Spec** — `cad.backend` matches kernel; `cad.parametric: true`.
6. **Rebuild/export** — emit `src/<body>.py` with named mm parameters. CadQuery: `docker run --rm -v "$PROJECT:/work" -w /work "$PREVERSE_STEP_IMAGE" python /work/src/<body>.py`. VibeCAD: `"$VIBECAD_CMD" src/<body>.py` or `POST /v1/run` (never commit the token). Write millimetre AP214 STEP + binary STL (`surface_deviation_mm` default 0.05). Refuse STEP if triangle-wrap, `parametric` with `fallback > 0`, or solid count ≠ `expected_shells`.
7. **Compare** — deterministic samples (stride + face centroids); `reports/<body>.deviation.json` with `max`, `mean`, `p95`, `n`, `max_deviation_mm`, `pass`. HARD if max exceeds budget.
8. **Gate** — spec validator + `validate_project.py` + compare. Pretty STEP with bad mesh topology is not done.

---

## Coupons and tests

`examples/bracket-coupon-reverse/`: `source/bracket-coupon.stl` (from existing OpenSCAD coupon), `docs/PRINT_SPEC.yaml`, `reverse/bracket.ir.json`, kernel `src/`, `stl/`, `reports/`. Commit IR + spec for unit tests. Do not commit huge STEP binaries.

Synthetic fixtures generated in tests (tiny ASCII cube may be committed): 20 mm cube → 6 planes / one extrude; plate + hole → extrude + cylinder; box + 5 mm chamfer; triangle-soup STEP → refuse.

Prompt `tests/prompts/stl-to-step-bracket.yaml`: “reverse engineer this STL to STEP” ranks `3d-print-reverse` above blender, shop-fixture, image-silhouette, vibecad. `run:` may be `no_cad` until tools exist; kernel steps skip when image/`VIBECAD_CMD` missing (same extra-extra style as `export_if_vibecad.py`).

Unit job: PyYAML + pytest only. Every behavior change has a focused test.

---

## Do not

- Onshape, Fusion, cloud converters, network APIs
- STEP from OpenSCAD or Blender; `csg2stp`; Assimp-from-mesh STEP
- Treat `mesh.to_shape` as success
- Vendor 10-X-eng/vibecad or AGPL converters into this repo
- Enable VibeCAD MCP; put an LLM in the geometry kernel
- Snap dimensions unless `--snap-mm`; parse `DESIGN.md`; waive HARD gates
- Merge this skill into openscad/blender; add it to `/3d-print`
- Pin `cadquery/cadquery:latest`; require host `pip install cadquery`

---

## Order of work

Each step leaves tests green. Do not start at STEP export.

1. Scaffold skill + empty CLI + contract/install/README/STATUS/prompt routing (`run: no_cad`).
2. Analyze + segment (cube/cylinder fixtures).
3. Sketch + features + PRINT_SPEC emit.
4. Deviation compare + triangle-wrap reject.
5. Emit CadQuery and VibeCAD/Part Python from IR (assert generated source; no Docker).
6. Track A: pinned CadQuery Docker extra extra (`export_if_cadquery.py` skips if image missing).
7. Stock VibeCAD coupon STEP export when `VIBECAD_CMD` is set.
8. Fork/PR 10-X-eng/vibecad for `mesh.reconstruct_parametric`. Printables only grows `--kernel vibecad`.
9. `examples/bracket-coupon-reverse` + `preverse gate`.
10. Prompt harness CAD path only if it needs no new unit-job deps.

---

## STATUS.md limits to record

- Reverse needs OCC. OpenSCAD/Blender cannot satisfy STEP.
- 10-X-eng/vibecad `mesh.to_shape` is faceted, not parametric. Fork the reconstruction pack.
- Default CI does not invoke VibeCAD. ARM qemu unsupported.
- v1 feature vocab is prismatic FDM. Organic scans may only reach `analytic`/`organic`.
- Proof is mesh deviation, not “this was the original CAD.”
- Fillet recovery is best-effort. Short STL chords stay warning-only.

---

## Working rules

Read this file, `CONTRIBUTING.md`, `tests/test_skill_contract.py`, `skills/3d-print-image-silhouette/`, `skills/3d-print-validate/scripts/`, and `skills/3d-print-vibecad/` before editing. Stdlib Python for analysis. Short factual comments. No secrets, home paths, or `__pycache__`. Missing STEP kernel → exit 2 on export; still ship analyze/IR tests.

```bash
python3 -m pytest -q \
  skills/3d-print-design-brief/tests \
  skills/3d-print-validate/tests \
  skills/3d-print-reverse/scripts/tests \
  tests/test_prompt_scenarios.py
python3 tests/test_skill_contract.py
```

## Checklist

- [ ] Skill publishes and passes `test_skill_contract.py`
- [ ] `preverse analyze|segment|sketch|features|spec|compare|gate` tested
- [ ] Cube and cylinder reconstruct without OCC
- [ ] Triangle-wrapped STEP refused
- [ ] Bracket coupon STL → IR → PRINT_SPEC → STL within `max_deviation_mm`
- [ ] STEP is analytic B-rep or export exits 2
- [ ] `--kernel vibecad` documented; CI skips unless `VIBECAD_CMD`
- [ ] VibeCAD coupon can emit STEP when the binary is present
- [ ] Named parameter change regenerates STL (and STEP when a kernel is present)
- [ ] README, STATUS, CONTRIBUTING, install.sh, CI, prompt scenario updated
- [ ] Unit CI still PyYAML + pytest only
