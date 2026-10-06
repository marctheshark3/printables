# Getting started

[Documentation](README.md) · [Skill catalog](../skills/README.md)

Run the commands below from the repository root after cloning.

## Install the pack

Python 3.11+ and PyYAML are enough to validate the committed examples. The installer also uses `rsync`. CAD backends have additional requirements listed below.

```bash
git clone https://github.com/marctheshark3/printables.git
cd printables
python3 -m pip install PyYAML
./install.sh
```

The installer discovers existing Hermes profiles. It copies the skills and `/3d-print` bundle additively, without deleting profile-local files. Start a new Hermes session after installation.

To preview installation or select profiles:

```bash
./install.sh --dry-run
HERMES_PROFILES=default ./install.sh
HERMES_PROFILES="default tron" ./install.sh
```

Only existing profiles are used. If none are found, the scripts remain usable from this checkout. `./install.sh --with-grok` also copies the skills into `$HOME/.grok/skills/`.

The installer includes every skill in the [catalog](../skills/README.md) except `3d-print-cad-render`, preserving any profile-local inspector. That inspector is usable from this checkout. The `/3d-print` bundle loads only the five core workflow skills.

## Use with Hermes

```text
/3d-print bracket for this sensor
```

The workflow writes and validates `docs/PRINT_SPEC.yaml`, builds parametric CAD, exports one STL per printable body, and validates the result. Other tasks, such as photo scaling, reverse engineering, instruction sheets, and slicing, have dedicated skills in the catalog.

## Use without Hermes

Validate a committed coupon; these commands do not invoke a CAD backend:

```bash
python3 skills/3d-print-design-brief/scripts/validate_print_spec.py \
  examples/bracket-coupon-vibecad/docs/PRINT_SPEC.yaml
python3 skills/3d-print-validate/scripts/validate_project.py \
  examples/bracket-coupon-vibecad
```

The spec validator should exit 0 and the project validator should report `HARD=0`. To work on your own exported project:

```bash
export PROJECT=/path/to/exported-project
python3 skills/3d-print-validate/scripts/validate_project.py "$PROJECT"
```

Continue with [design and validation](guides/design-and-validation.md) or the [example projects](../examples/README.md).

## Set up a CAD backend

| Task | Requirement |
|---|---|
| Dimensional mechanical CAD | Host [10-X-eng/vibecad](https://github.com/10-X-eng/vibecad), using `VIBECAD_CMD` or `FREECAD_CMD` |
| Portable exports, CI samples, or a request naming OpenSCAD | OpenSCAD; CI uses `openscad/openscad:2021.01` in Docker |
| Organic or lattice geometry | Blender 4.x |
| STEP inspection | Host `FreeCADCmd` via `FREECAD_CMD` or `VIBECAD_CMD`; an existing OCC scene dump can be packed without the binary |
| STL reconstruction to STEP | An OCC kernel; see [existing parts](guides/existing-parts.md#rebuild-an-stl-as-editable-step) |

VibeCAD is the dimensional kernel. Use the 10-X-eng project, not the PyPI package named `vibecad` or upstream FreeCAD. The pack does not vendor a CAD binary.

```bash
python3 skills/3d-print-vibecad/scripts/find_vibecad.py status
python3 skills/3d-print-vibecad/scripts/find_vibecad.py download   # x86_64 only
```

Set `VIBECAD_CMD` to the command reported by the helper. Linux ARM with a qemu-x86_64 AppImage is unsupported. See the [VibeCAD host instructions](../skills/3d-print-vibecad/references/vibecad-host.md) and [known limits](status.md#known-limits) before exporting.

Photo processing and slicing have optional dependencies documented in their guides. For development dependencies and checks, see [tests](../tests/README.md).
