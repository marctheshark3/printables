# Printables

Deterministic CAD/CAM for FDM: agents write one contract, build the part, export one STL per independently manufactured body, then fail closed. VibeCAD is the dimensional kernel. A loopback STEP inspector ships in this repo. A render is not print approval.

```text
PRINT_SPEC.yaml → VibeCAD → one STL per body → validate_project.py → validate_assembly.py
                         ↘ STEP → 3d-print-cad-render (loopback inspector)
```

Markdown is narrative only. `docs/DESIGN.md` is never parsed. An assembly is multiple `geometry.stl_files` entries.

OpenSCAD is not the dimensional kernel. It stays in the tree for CI sample exports, a prompt that names OpenSCAD, and hosts where VibeCAD cannot run. Upstream FreeCAD is not a supported kernel. Blender is organic or lattice only.

## Skill names

All tools use the same prefix, followed by one obvious job:

- `3d-print-design-brief` — define and validate the manufacturing contract
- `3d-print-vibecad` — dimensional mechanical CAD in 10-X-eng/vibecad. Not the PyPI package. Not upstream FreeCAD.
- `3d-print-openscad` — portable and CI export path. OpenSCAD is not the dimensional kernel.
- `3d-print-blender` — organic or lattice CAD; exception backend
- `3d-print-validate` — contract and STL validation
- `3d-print-display-enclosure` — small two-piece display enclosures
- `3d-print-robotics` — numbered FDM micro-robotics kit modules
- `3d-print-sim` — assembled occupancy, joint sweep, and load section check
- `3d-print-image-silhouette` — image-derived stencils and silhouettes
- `3d-print-photo-cad` — millimetres from a printed ChArUco photo. Not a caliper. Not in `./install.sh`.
- `3d-print-shop-fixture` — decide whether a shop fixture should be printed or bought
- `3d-print-reverse` — rebuild an existing STL as editable STEP and a gated STL
- `3d-print-pack` — zip a gated project (spec, source, STLs, print notes, manifest)
- `3d-print-slice` — process card from PRINT_SPEC; optional 3MF if a slicer CLI is present
- `3d-print-cad-render` — loopback STEP inspector (parts tree, measure, OCC faces and BREP edges). Not a mill. Not in `./install.sh`, so a profile-local copy is not overwritten.

The `/3d-print` bundle loads the brief, VibeCAD, OpenSCAD, Blender, and the validator. Dimensional work uses VibeCAD. Use OpenSCAD only when the prompt names it, for CI sample STL export, or when VibeCAD cannot run. Blender is organic or lattice only. `3d-print-cad-render`, `3d-print-reverse`, `3d-print-pack`, and `3d-print-slice` are not required by `/3d-print`. Live printer control is the sibling `bambu-mcp` repo; this pack never stores access codes, serials, or LAN IPs.

VibeCAD (10-X-eng/vibecad, not the PyPI package) uses the same PRINT_SPEC and `validate_project` gates. This pack does not vendor it. Linux ARM qemu-x86_64 AppImage is not supported. Boolean welding of overlapping solids stays a known limit until a live one-solid export. Set `VIBECAD_CMD` or `FREECAD_CMD` to the host `FreeCADCmd`. Do not point that variable at upstream FreeCAD.

## Hard contract

Each project owns `docs/PRINT_SPEC.yaml` with:

- `cad.parametric: true`
- backend chosen from `vibecad` (dimensional default), `openscad` (portable or CI), `blender`, `hybrid`, or optional `cadquery`
- millimetres and Z-up
- explicit X/Y/Z printer build volume
- named CAD parameter for each critical dimension
- nominal value, tolerance, and provenance for each dimension
- one STL per independently manufactured body (an assembly is several entries)
- expected watertight shell count per STL
- overlapping exported solids forbidden
- minimum wall and feature sizes
- clearance stated per side
- fit evidence and coupon policy
- print orientation, bed face, support policy, and overhang limit
- service material and drainage requirements

## Install

Requirements: Linux for CAD backends; Python 3.11+; PyYAML. Dimensional export and STEP dumps need a host `FreeCADCmd` via `VIBECAD_CMD` or `FREECAD_CMD` (10-X-eng/vibecad, not upstream FreeCAD). Docker OpenSCAD is only the CI and portable path. Blender 4.x is only the Blender backend.

```bash
git clone https://github.com/marctheshark3/printables.git
cd printables
python3 -m pip install PyYAML pytest
./install.sh
./install.sh --dry-run
HERMES_PROFILES=default ./install.sh
```

Installation is additive and never deletes profile-local files. Start a new Hermes session after installation.

Optional 10-X-eng/vibecad binary. This pack does not vendor it. Linux ARM qemu-x86_64 AppImage is not supported:

```bash
python3 skills/3d-print-vibecad/scripts/find_vibecad.py status
python3 skills/3d-print-vibecad/scripts/find_vibecad.py download   # x86_64 only
export VIBECAD_CMD=...   # printed by the command
```

## Use

```text
/3d-print bracket for this sensor
```

Without Hermes:

```bash
python3 skills/3d-print-design-brief/scripts/validate_print_spec.py \
  examples/bracket-coupon/docs/PRINT_SPEC.yaml

python3 skills/3d-print-validate/scripts/validate_project.py \
  /path/to/exported-project

python3 skills/3d-print-validate/scripts/validate_assembly.py \
  examples/robot-kit-01-rover

python3 skills/3d-print-validate/scripts/validate_assembly.py \
  examples/robot-kit-01-rover-v2

python3 skills/3d-print-validate/scripts/validate_assembly.py \
  examples/robot-kit-01-rover-kid

python3 skills/3d-print-sim/scripts/roll_table_flat.py \
  examples/robot-kit-01-rover
```



For reverse engineering an existing STL to editable STEP:

```bash
skills/3d-print-reverse/scripts/preverse run --stl in.stl --project "$PROJECT"
```

STEP export needs OCC (`VIBECAD_CMD` or a pinned `PREVERSE_STEP_IMAGE` digest). Analyze through gate does not. Missing kernel exits 2 and never writes a fake STEP.

For the loopback inspector (`3d-print-cad-render`):

```bash
export QT_QPA_PLATFORM=offscreen
export FREECAD_CMD=/path/to/FreeCADCmd
python3 skills/3d-print-cad-render/scripts/render_cad_project.py \
  --project "$PROJECT" --serve --port 8107
```

Loopback only: `http://127.0.0.1:8107/?view=solid`. This pack does not ship a network proxy or a FreeCAD binary. An STL is not a CAD view. The inspector is not a mill and not print approval. `./install.sh` does not copy this skill.

For Blender:

```bash
skills/3d-print-blender/scripts/pblend new organic-lid --class enclosure
skills/3d-print-blender/scripts/pblend run --project "$HOME/print-projects/organic-lid"
skills/3d-print-blender/scripts/pblend gate --project "$HOME/print-projects/organic-lid"
```

## Validation

`validate_project.py` fails closed on:

- incomplete or contradictory contract
- missing source or STL
- absolute or parent-traversal project paths
- non-parametric backend declaration
- open, non-manifold, inconsistently oriented, duplicate, or degenerate topology
- wrong connected-shell count
- overlapping exported solids
- non-positive volume
- build-volume overflow
- unacceptable fit or wet-service evidence
- class-specific overhang and open-under failures
- sampled wall thickness below `geometry.min_wall_mm` over more than `thin_wall_area_frac=0.02` of sampled area

When `assembly` is present, `validate_assembly.py` then fail-closes on illegal assembled occupancy, joint self-collision, and missing or assumed required loads. A render is not proof.

`sim2real: true` requires mass, friction, and actuator calibration coupons with measured or datasheet sources. Assumed calibration cannot claim sim2real. A MuJoCo window is not the contract.

Short STL chords are tessellation, not wall thickness. They remain warning-only. Mesh thickness is a sampled inward-ray audit, not an exact-kernel proof.

After HARD=0, `3d-print-pack` writes a deliverable zip. `3d-print-slice` always writes a process card and skips 3MF with `SKIP: no slicer CLI` when no slicer is configured. A validated STL is not permission to print.

## Tests

```bash
python3 -m pytest -q skills/3d-print-design-brief/tests skills/3d-print-validate/tests skills/3d-print-reverse/scripts/tests skills/3d-print-vibecad/scripts/tests skills/3d-print-pack/scripts/tests skills/3d-print-slice/scripts/tests skills/3d-print-cad-render/tests skills/3d-print-image-silhouette/tests skills/3d-print-photo-cad/tests tests/test_prompt_scenarios.py tests/test_secret_scan.py
python3 tests/test_skill_contract.py
python3 tests/prompt_harness.py
python3 -m unittest discover -s skills/3d-print-blender/scripts/tests -v
python3 -m py_compile \
  skills/3d-print-design-brief/scripts/*.py \
  skills/3d-print-validate/scripts/*.py \
  skills/3d-print-sim/scripts/*.py \
  skills/3d-print-blender/scripts/pblend_cli.py \
  skills/3d-print-image-silhouette/scripts/*.py \
  skills/3d-print-reverse/scripts/*.py \
  skills/3d-print-pack/scripts/*.py \
  skills/3d-print-slice/scripts/*.py \
  skills/3d-print-vibecad/scripts/find_vibecad.py \
  skills/3d-print-cad-render/scripts/*.py \
  skills/3d-print-photo-cad/scripts/*.py
```

`tests/prompts/` holds sample user prompts. CI ranks them onto skills, then the `generate-stls` job exports real STLs with OpenSCAD/Blender and uploads them as the `generated-stls` artifact. That job is the portable export path, not the dimensional kernel. Shop-fixture prompts stop at buy-vs-print. Inspector and VibeCAD binary steps are not invoked unless `FREECAD_CMD` or `VIBECAD_CMD` is set. No live model.

## License

MIT. See [LICENSE](LICENSE).
