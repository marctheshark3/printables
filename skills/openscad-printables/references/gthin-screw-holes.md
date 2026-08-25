# G-thin vs screw-hole tessellation

G-thin HARD is an **edge-length** heuristic, not a wall-thickness test.

Ø4.6 mm hole at `$fn=32` → chord ≈ π×4.6/32 ≈ 0.45 mm → frac of edges < 0.50 mm trips HARD even when walls are 4.5 mm.

Fix in CAD: `$fn=20` on fastener holes (chord ≈ 0.72 mm). Pegs Ø8 at `$fn=20` are fine.

Do **not** raise `dfm_gate --thin-fail-frac` to hide hole chords. Soft-mode / 0.35 frac remains for organic tessellation only.

Re-export and re-gate after the `$fn` change. Husky sheet-rack v4: all seven STLs PASS at `$fn=20`.
