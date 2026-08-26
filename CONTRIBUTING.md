# Contributing

This pack is executed by coding agents. Keep behavior deterministic and validation fail-closed.

## Source of truth

Edit this repository, run the complete checks, then install into local Hermes profiles. Do not treat a profile copy as canonical.

## What belongs here

- portable skill prose and machine-readable contracts
- parametric scaffolds and backend CLIs
- backend-neutral STL validation
- generic examples with invented dimensions
- sample prompts under `tests/prompts/` that CI routes and executes
- tests that run without Docker, Blender, or private fixtures

## What does not

- credentials, tokens, private hostnames, or machine-local paths
- household geometry, photos, queues, or inventory
- a CAD backend that cannot satisfy the same contract
- aliases for deleted skill names
- a relaxed HARD gate added only to make a failing artifact pass

## Checks before a PR

```bash
python3 -m pip install PyYAML pytest
python3 -m pytest -q skills/3d-print-design-brief/tests skills/3d-print-validate/tests tests/test_prompt_scenarios.py
python3 tests/prompt_harness.py   # OpenSCAD Docker + Blender; writes artifacts/stls/
python3 -m unittest discover -s skills/3d-print-blender/scripts/tests -v
python3 tests/test_skill_contract.py
python3 skills/3d-print-design-brief/scripts/validate_print_spec.py \
  examples/bracket-coupon/docs/PRINT_SPEC.yaml
python3 skills/3d-print-design-brief/scripts/validate_print_spec.py \
  examples/robot-kit-01-rover/docs/PRINT_SPEC.yaml
python3 skills/3d-print-validate/scripts/validate_project.py \
  examples/robot-kit-01-rover
```

Also run the private-path and secret scan from `.github/workflows/ci.yml`.

## Change rules

- Every behavior change needs a focused test.
- Every published skill name begins with `3d-print-`.
- Descriptions are one sentence, at most 60 characters, ending in a period.
- Every `related_skills` entry must resolve in this repository.
- OpenSCAD remains the dimensional default.
- Blender is an exception for organic or lattice bodies.
- HARD validation failures block delivery.
