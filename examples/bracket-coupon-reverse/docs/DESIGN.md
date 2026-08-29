# Reverse L-bracket coupon

Narrative only. The machine contract is `docs/PRINT_SPEC.yaml`. The rebuild input is `reverse/bracket.ir.json`. This file is never parsed.

The input STL is a reference mesh copied from the OpenSCAD coupon. Reconstruction uses sketches and features (extrude + three holes). Triangle-wrapped STEP is HARD.

Default unit CI does not invoke VibeCAD, CadQuery, Docker, or OCC. Live analytic STEP is extra extra when `VIBECAD_CMD` or a pinned `PREVERSE_STEP_IMAGE` digest is set.
