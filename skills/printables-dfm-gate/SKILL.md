---
name: printables-dfm-gate
description: "Use after OpenSCAD export to fail-closed gate an STL before claiming it is printable. Checks welded-edge topology, intended component count, fit and wet-service metadata, bed fit, coarse overhangs, and open-under equipment rules. Part of /printables."
license: MIT
metadata:
  version: "1.1.0"
  author: Tron
  platforms: linux
  hermes:
    tags: [dfm, 3d-print, stl, validation, manufacturing, bambu, p1s, printables]
    related_skills: [openscad-printables, printables-part-brief]
---

# Printables DFM Gate — fail closed

## Overview

Close the manufacturing loop with **machine checks**, not skill prose. A readable STL is not sufficient: welded-edge topology, shell count, declared fit evidence, and service-specific gates are part of the contract. After Docker STL export, run gates. **Non-zero exit = not done.** Redesign or get Marc override.

Scripts live with `openscad-printables` (shared pack scripts):

```
<skill>/scripts/validate_export.sh
<skill>/scripts/dfm_gate.py
```

## When to Use

- After every STL export on a printables job
- Before Discord zip / “done”
- Skill regression on `dgx-spark-stand`
- Anytime Marc says “is this actually printable?”

## Procedure

1. Ensure project has `docs/DESIGN.md` with `product_class`, `print_orientation`, `expected_components`, and fit/service metadata (from part-brief).
2. Export STL (Docker) if not fresh.
3. Run:

```bash
SKILL="$(…/openscad-printables)"   # pack or installed creative path
"$SKILL/scripts/validate_export.sh" "$PROJECT" <version-or-basename>
# validate_export invokes dfm_gate.py when present
```

Direct DFM-only:

```bash
python3 "$SKILL/scripts/dfm_gate.py" \
  --project "$PROJECT" \
  --stl "$PROJECT/stl/<part>.stl" \
  --mode-file "$PROJECT/docs/DESIGN.md"
```

4. On HARD fail → fix SCAD (or orientation/class), re-export, re-gate. Do not ship.
5. On WARN only → report to Marc; may ship if intentional.
6. On PASS → previews + print notes + **zip STL**.

## Gate map

| ID | Severity | Checks |
|----|----------|--------|
| G1–G3 | HARD | source, STL, mesh parse |
| G-topology | HARD | welded boundary/non-manifold/orientation edges, duplicate/degenerate faces |
| G-components | HARD | edge-connected shell count matches `expected_components` |
| G-fit | HARD | required fit lacks measured/from-user/fit-tested evidence |
| G-wet | HARD | wet service lacks drainage or declares PLA/unspecified material |
| G5 / G5b | HARD | bbox limits / P1S bed &lt; 256 mm |
| G6 | HARD when gold | volume band |
| G7 | HARD when open-frame gold | SCAD open-frame language; pin smell |
| G8 | WARN | orientation language in docs |
| G-mode | HARD | DESIGN.md product_class + print_orientation |
| G-orient | HARD | print_up_axis resolvable |
| G-overhang | HARD if area large | faces &gt; overhang_max vs print-up |
| G-tessellation | WARN | unusually many short STL chords; not a wall-thickness test |
| G-open-under | HARD for equipment-open-frame | solid fraction under seating Z-band too high |
| G-density | WARN | unusually dense mesh |

## Soft vs hard policy

- **HARD:** block deliver; agent must not claim done
- **WARN:** include in report; Marc can accept
- **Override:** only if Marc explicitly waives a named gate in-thread — record in DESIGN.md `gate_override:`

## Completion criteria

- [ ] validate_export exit 0 (or documented override)
- [ ] dfm_gate HARD count = 0
- [ ] topology is closed and component count matches design intent
- [ ] fit and wet-service declarations pass when applicable
- [ ] minimum walls/features are verified in CAD or slicer; STL chord length is not used as proof
- [ ] volume cm³ reported
- [ ] print notes include orientation + flip + supports expectation

## Common pitfalls

1. Shipping after Docker export without running gates  
2. Treating `Volumes: 2` as failure (healthy single solid in OpenSCAD 2021.01)  
3. Ignoring G-open-under by reclassifying equipment as tray without intent change  
4. Disabling overhang check instead of fixing orientation/structure  
5. Claiming “looks fine in preview” over mesh gates  
6. Treating OpenSCAD `Volumes` output as a topology or component-count proof  
7. Hiding an assumed critical fit behind a generous clearance without documenting it  

## Verification checklist

- [ ] Gates run on the STL being delivered  
- [ ] HARD fails addressed  
- [ ] Stand regression still green after skill changes  
