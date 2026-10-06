# Documentation

Start with [getting started](getting-started.md) to install the pack and validate an example. Browse the [skill catalog](../skills/README.md) when you know the job you want to do.

## Guides

| Task | Guide |
|---|---|
| Define a part, choose CAD, and check the result | [Design and validation](guides/design-and-validation.md) |
| Inspect STEP geometry or make assembly sheets | [Inspection and instructions](guides/inspection-and-instructions.md) |
| Work from a photo or rebuild an existing STL | [Existing parts](guides/existing-parts.md) |
| Package a validated project and prepare slicer output | [Pack and slice](guides/pack-and-slice.md) |

Commands in these guides run from the repository root. `PROJECT` means the directory containing your part's `docs/PRINT_SPEC.yaml`, CAD source, and exported bodies.

## Reference

- [PRINT_SPEC contract](../skills/3d-print-design-brief/references/print-spec-v1.md) — fields, dimensions, provenance, and validation rules.
- [Project status](status.md) — supported behavior and known limits.
- [Examples](../examples/README.md) — bracket coupons and the rover family.
- [Tests](../tests/README.md) — local checks and CI commands.
- [Contributing](../CONTRIBUTING.md) — repository scope and change rules.

## Repository layout

```text
docs/           Setup, guides, status, images, and archived plans
skills/         Skill catalog and self-contained skill packages
skill-bundles/  The /3d-print workflow definition
examples/       Sample projects with their own PRINT_SPEC and source
tests/          Repository checks and prompt scenarios
```

Each skill keeps its `SKILL.md`, scripts, tests, templates, and references together. The installer and cross-skill tools use the existing `skills/3d-print-*` paths.

## Archive

These completed implementation plans preserve the original method and scope. They are historical records, not a backlog:

- [STL to editable STEP](archive/stl-to-step.md)
- [Manufacturing after STL export](archive/post-stl.md)

[Back to Printables](../README.md)
