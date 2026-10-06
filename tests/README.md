# Tests

[Contributing](../CONTRIBUTING.md) · [Documentation](../docs/README.md)

Run these commands from the repository root. The unit checks need Python 3.11+, PyYAML, and pytest; CAD export checks have separate dependencies.

## Unit checks

```bash
python3 -m pip install PyYAML pytest
python3 -m pytest -q \
  skills/3d-print-design-brief/tests \
  skills/3d-print-validate/tests \
  skills/3d-print-reverse/scripts/tests \
  skills/3d-print-vibecad/scripts/tests \
  skills/3d-print-pack/scripts/tests \
  skills/3d-print-slice/scripts/tests \
  skills/3d-print-cad-render/tests \
  skills/3d-print-lego-instructions/tests \
  skills/3d-print-ikea-instructions/tests \
  skills/3d-print-image-silhouette/tests \
  skills/3d-print-photo-cad/tests \
  tests/test_prompt_scenarios.py \
  tests/test_secret_scan.py
python3 -m unittest discover -s skills/3d-print-blender/scripts/tests -v
python3 tests/test_skill_contract.py
```

The skill contract check covers names, metadata, routing, installation, and published behavior. The secret scan checks public skills and documentation, with historical examples of forbidden values excluded in `docs/archive/`.

## Example contracts and geometry

Validate every committed example contract:

```bash
for project in examples/*/; do
  python3 skills/3d-print-design-brief/scripts/validate_print_spec.py \
    "$project/docs/PRINT_SPEC.yaml" || exit 1
done
```

Check the examples with committed STLs:

```bash
for project in examples/bracket-coupon-vibecad examples/bracket-coupon-reverse \
  examples/robot-kit-01-rover examples/robot-kit-01-rover-v2 \
  examples/robot-kit-01-rover-kid; do
  python3 skills/3d-print-validate/scripts/validate_project.py "$project" || exit 1
done
```

Check the three rover assemblies and calibration reports:

```bash
for project in examples/robot-kit-01-rover examples/robot-kit-01-rover-v2 \
  examples/robot-kit-01-rover-kid; do
  python3 skills/3d-print-validate/scripts/validate_assembly.py "$project" || exit 1
  python3 skills/3d-print-sim/scripts/roll_table_flat.py "$project" || exit 1
done
```

The OpenSCAD coupon requires export before project validation; see [examples](../examples/README.md#openscad-coupon).

## Python compilation

```bash
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
  skills/3d-print-lego-instructions/scripts/*.py \
  skills/3d-print-ikea-instructions/scripts/*.py \
  skills/3d-print-photo-cad/scripts/*.py
```

## Prompt routing and CAD exports

[`tests/prompts/`](prompts/README.md) contains sample requests and their expected skill routes. `test_prompt_scenarios.py` checks routing without a live model.

```bash
python3 tests/prompt_harness.py
```

The harness runs available CAD tools and reports skips for missing local tools. To require CAD export, matching CI:

```bash
PRINTABLES_GENERATE_STLS=1 python3 tests/prompt_harness.py
```

The [`generate-stls` CI job](../.github/workflows/ci.yml) uses Docker OpenSCAD and headless Blender to export real STLs into `artifacts/stls/`, then uploads the `generated-stls` artifact. Shop-fixture prompts stop at the buy-or-print decision. VibeCAD binary and STEP kernel runs are optional; the default unit job does not invoke them. Real photo processing and slicer CLIs are also outside unit CI.

Before a PR, also run the private-path and secret scan in [the CI workflow](../.github/workflows/ci.yml).
