# Iteration protocol (stop designs getting worse)

Root failure mode from prior sessions: **first shot good → each “improve for 3D printing / change X” rewrote language until form + printability both suffered.**

This protocol is mandatory for any redesign after v1 exists.  
**Canonical proof history:** `dgx-spark-stand` v1→v9 (see `regression-test-stand.md`).

## 1. Lock form language before CAD edits

Write (or update) `docs/DESIGN_vN.md` with:

- **Intent card** (see `intent-lock-and-variants.md`) if product class might drift.
- **Form language lock:** e.g. “soft hex tray, plan_r=18, open rear, open-frame empty under” — what Marc liked.
- **Change budget:** at most 1–3 explicit goals this iteration.
- **Non-goals:** what we will **not** reinvent (don’t turn open frame into pin forest or X-frame).
- **Orientation lock:** **TOP-FIRST** (default elevated) or feet-down explicit.

If Marc liked vN form, **start from that SCAD**, not a blank “clever” rewrite.

## 2. Diff-only discipline

1. Copy `src/foo_vN.scad` → `src/foo_vN+1.scad` (or keep one file + git).
2. Change only what the budget lists.
3. Keep the same module names and param block structure when possible.
4. Echo version string + key params + orientation every render.

## 3. Hard gates before “ready”

Every iteration must report:

| Gate | Pass criterion |
|------|----------------|
| Manifold | OpenSCAD / validation **Simple: yes** |
| Volumes | Prefer **Volumes: 2** (explain if higher) |
| Bbox | Fits target printer with margin |
| Volume | cm³ reported **and** vs previous version |
| Form language | Soft / open-frame still true if locked |
| Structure | No mid-air beams; no pin forest under equipment |
| Orientation | TOP-FIRST vs feet-down matches DESIGN |
| Supports claim | Honest (supports off only if structure justifies) |
| Previews | Contact sheet + under/cutaway if structure changed |

If a gate fails, fix before proposing a new creative direction.

For the skill fixture, also run:

```bash
scripts/validate_export.sh ~/Documents/the-grid/dgx-spark-stand v9 --stl-only
```

## 4. Regression table

Update a small table in DESIGN.md:

| Ver | Intent | Volume | Simple | Verdict |
|-----|--------|--------|--------|---------|
| v1 | liked form | … | … | baseline |
| … | … | … | … | … |

Never delete the “liked form” baseline from docs.

## 5. When Marc says it got worse

1. Stop. Identify which change budget item broke form or printability.
2. **Revert form language** to last liked silhouette.
3. Re-apply only the missing DFM on that silhouette.
4. Do not invent a third product category.

### 5b. When Marc rejects the whole form (“this ain’t it” / different version / from scratch)

This is **not** §5 (tweak liked form). Treat as **new product class**:

1. Stop polishing the hated silhouette.
2. If stack/hardware fixture: **research community designs** first — lock takeaways in DESIGN.
3. New form language lock + change budget; new `src/*_vN.scad` (or new project dir if from-scratch).
4. Still apply durable DFM laws (open under bottom-vent gear, no pin forest, TOP-FIRST, chassis clearance, Volumes:2).
5. Do **not** “improve” the rejected tower/cage by adding more of the same language.

## 6. Parameter surface for safe tweaks

Prefer exposing knobs Marc can request by name:

```
fit_clearance, wall, clearance_z, plan_r,
hex_r, hex_bar, pillar_w, edge_beam_w,
window_margin, lip_h, pip_gap, bed_chamfer
```

Avoid advertising `stilt_pitch` as a default knob for equipment bases.

Re-export with Docker `-D` instead of surgical rewrites when possible.

## 7. Anti-patterns (instant reject)

- Full rewrite “from scratch” without form language lock when a liked version exists
- Mid-air “minimal frame” as DFM fix
- Solid-filling cavity to “make it printable” without volume callout
- Square language after soft mode was locked
- Claiming supports-off after removing necessary structure
- Shipping without volume + Simple + multi-view
- **Pin stilts or waffle under bottom-vent equipment** “for printability”
- Treating TOP-FIRST request as a new silhouette license
