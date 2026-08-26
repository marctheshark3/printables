# Image context protocol (optional reference media)

## When an image is present

1. Locate path (Discord cache, `HERMES_HOME/cache/images/`, user path, attachment).
2. Call **`vision_analyze`** on that path — do not invent geometry from filename alone.
3. Record findings in `docs/PRINT_SPEC.yaml` (dimensions + provenance) and optional narrative in `docs/DESIGN.md`.

## Classify image role

| Role | Meaning | Dims policy |
|------|---------|-------------|
| `metrology` | User expects size from photo (ruler, known object, datasheet screenshot) | Extract scale if possible; still tag uncertainty |
| `style` | Aesthetic / silhouette only | No tight dims from photo |
| `context` | Show mating hardware / port layout | Capture features + keep-outs; loose clearances |

Put the role in `part.purpose` or DESIGN.md prose. Do not invent a second machine frontmatter.

## What to extract

- Object identity and mating faces
- Ports, vents, bottom airflow (critical for open-frame class)
- Approximate aspect ratio / proportions
- Known objects for scale (credit card, coin, chassis model name)
- Keep-outs (cables, fans, screw heads)

## What never to do

- Invent ±0.1 mm tolerances from one phone photo
- Assume feet-down print just because the photo shows use orientation
- Skip PRINT_SPEC.yaml because “the image is clear enough”
- Treat style refs as mechanical drawings

## Default clearances when scale is uncertain

- Loose fit FDM: **0.5–1.0 mm/side** (stands often **0.8**)
- Min solid feature: **≥ 1.6 mm** (0.4 mm nozzle family)
- Every assumed dimension is a PRINT_SPEC row with `source: assumed`
