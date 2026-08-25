# Form rejects (Marc visual QA)

Do not ship / do not polish these — **rewrite geometry**.

| Reject | Looks like | Fix |
|--------|------------|-----|
| Nested offset cavity | Soap dish / pyramid floor | Single flat cavity extrude |
| Bezel side cubes | Torn picture frame corners | I/O only on base walls |
| Bezel plug −Z | Overhang fail / wrong print | Face bed, plug +Z |
| Capsule Voronoi lid | Stick soup | Plate + joined cutters |
| Voxel fatten shell | Melted CAD | light cleanup only |
| Random tilt tab | Broken heel under case | tilt=false or separate stand |
| Gate PASS only | “Yikes” stills | vision_analyze halves first |

Themed Adafruit/X cases (floppy, LCARS) ≠ utility lab COP brief.
