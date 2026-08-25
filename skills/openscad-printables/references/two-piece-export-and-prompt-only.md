# Two-piece export + prompt-only CAD

## Two-piece STLs

Never gate `which=assembly` — that is two shells. Export separately:

```bash
docker run --rm -v "$PROJECT:/work" -w /work openscad/openscad:2021.01 \
  openscad -o /work/stl/part-base.stl --export-format=binstl \
  -D 'which="base"' /work/src/part.scad
# same for which="bezel"
```

`expected_components: 1` **per file**. PyPortal helper: `~/Documents/the-grid/pyportal-desk-case/scripts/export_stl.sh`.

## Prompt-only vs skills (grok-4.6, 2026-08-15)

A locked brief + raw 4.6 (no printables pack) can **compile and DFM HARD=0**. That is not print-ready: cube brick, no mount posts, no speaker vent, sharp bezel.

Print the skills remake. Bench: skill `estate-llm-bakeoff` → `references/printables-scad-bench.md`.
