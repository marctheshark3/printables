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

Run the [unit checks, example validation, compilation, and CAD prompt harness](tests/README.md), plus the private-path and secret scan from [CI](.github/workflows/ci.yml). The testing guide separates checks that need only Python from those that need CAD tools.

## Where things belong

- Keep the [README](README.md) focused on the introduction, quick start, and navigation.
- Put shared walkthroughs in `docs/guides/` and link them from the [documentation index](docs/README.md).
- Keep supported behavior and known limits in [project status](docs/status.md). Completed implementation plans belong in `docs/archive/`.
- Keep each skill's instructions, scripts, tests, templates, and references together under `skills/3d-print-*/`. The installer and scripts depend on these paths.
- Update the [skill catalog](skills/README.md) when a skill is added or its purpose changes.
- Put runnable sample projects in `examples/` and development commands in [tests](tests/README.md).

## Change rules

- Every behavior change needs a focused test.
- Every published skill name begins with `3d-print-`.
- Descriptions are one sentence, at most 60 characters, ending in a period.
- Every `related_skills` entry must resolve in this repository.
- VibeCAD is the dimensional kernel (10-X-eng/vibecad). Not upstream FreeCAD. Not the PyPI package.
- OpenSCAD is not the dimensional kernel. Keep it for CI sample exports, a named OpenSCAD prompt, and hosts where VibeCAD cannot run.
- `3d-print-cad-render` is the loopback STEP inspector. It is not in `/3d-print` and not in `./install.sh`.
- `3d-print-lego-instructions` is the picture step-sheet skill. It is in `./install.sh` and not in `/3d-print`.
- `3d-print-ikea-instructions` is the required-sequence skill. It is in `./install.sh` and not in `/3d-print`. A named style wins.
- Blender is an exception for organic or lattice bodies.
- Reverse (`3d-print-reverse`) is optional and is not in `/3d-print`. Do not vendor 10-X-eng/vibecad.
- Pack and slice are optional and are not in `/3d-print`. Do not vendor `bambu-mcp`. Do not commit printer access codes, serials, or LAN IPs.
- HARD validation failures block delivery.
