# Printables

Deterministic CAD/CAM for FDM: agents write one contract, pick a CAD backend, export one STL per independently manufactured body, then fail closed.

```text
PRINT_SPEC.yaml → CAD backend → one STL per body → validate_project.py
```

Markdown is narrative only. `docs/DESIGN.md` is never parsed. An assembly is multiple `geometry.stl_files` entries.

## Skill names

All tools use the same prefix, followed by one obvious job:

- `3d-print-design-brief` — define and validate the manufacturing contract
- `3d-print-openscad` — dimensional mechanical CAD; default backend
- `3d-print-blender` — organic or lattice CAD; exception backend
- `3d-print-validate` — contract and STL validation
- `3d-print-display-enclosure` — small two-piece display enclosures
- `3d-print-image-silhouette` — image-derived stencils and silhouettes
- `3d-print-shop-fixture` — decide whether a shop fixture should be printed or bought

The `/3d-print` bundle loads the brief, OpenSCAD, Blender, and validator. Use OpenSCAD for dimensional work and Blender only for organic or lattice bodies.

VibeCAD is not shipped. Its current Linux ARM/headless path and boolean behavior do not meet this pack's reliability contract.

## Hard contract

Each project owns `docs/PRINT_SPEC.yaml` with:

- `cad.parametric: true`
- backend chosen from `openscad`, `blender`, or `hybrid`
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

Requirements: Linux for CAD backends; Python 3.11+; PyYAML; Docker for pinned OpenSCAD; Blender 4.x only for the Blender backend.

```bash
git clone https://github.com/marctheshark3/printables.git
cd printables
python3 -m pip install PyYAML pytest
./install.sh
./install.sh --dry-run
HERMES_PROFILES=default ./install.sh
```

Installation is additive and never deletes profile-local files. Start a new Hermes session after installation.

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
```

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

Short STL chords are tessellation, not wall thickness. They remain warning-only; minimum walls come from CAD parameters and slicer verification.

## Tests

```bash
python3 -m pytest -q skills/3d-print-design-brief/tests skills/3d-print-validate/tests tests/test_prompt_scenarios.py
python3 tests/prompt_harness.py
python3 -m unittest discover -s skills/3d-print-blender/scripts/tests -v
python3 -m py_compile \
  skills/3d-print-design-brief/scripts/*.py \
  skills/3d-print-validate/scripts/*.py \
  skills/3d-print-blender/scripts/pblend_cli.py
```

`tests/prompts/` holds sample user prompts. CI ranks them onto skills, then runs the real spec/mesh tools (or asserts a buy-vs-print stop). No live model. Add a YAML there when you add a skill path.

## License

MIT. See [LICENSE](LICENSE).
