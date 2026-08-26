---
name: 3d-print-shop-fixture
description: Decide whether to print or buy a shop fixture.
version: 1.0.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [3d-print, shop, bun-pan, husky, dfm, buy-vs-print]
    related_skills: [3d-print-design-brief, 3d-print-openscad, 3d-print-validate]
---

# Print vs buy — shop fixtures

Class skill for **storage/work fixtures** (under-desk trays, wall slides, carts). Not one-off enclosure CAD.

Pair with `3d-print-design-brief` for a validated `PRINT_SPEC.yaml`; route printable clips through `3d-print-openscad` and `3d-print-validate`.

## When to use

- Baking / bun / sheet-pan as project trays
- Under-desk, wall, or cart electronics storage
- User says a print is not practical or too much material
- Sit/stand or drawer-bench mounts

## Decision order (forced)

1. **Buy the tray.** Commercial half sheet **13×18**, bare aluminum, **wire-in rolled rim**. Never print the pan. Skip nonstick and perforated.
2. **Print only L-slides/clips** (`bracket`, ~6 copies, tens of grams) if a static mount exists: wood-top **wings**, static legs, or wall into a 1x4.
3. **Buy the rack** if clips are hassle: half-height 10-pan bun cart (~26×20×38, ~$80) parked **beside** the bench. Skip full 20-tier (~70" / $110–150) and commercial wall 5-pan (~$138) unless wall is the only remaining option.

Do not CAD a floor tower, cage, or “printed speed rack.”

## Sit/stand + drawers

Crank **moves the top**. Do not screw hangers into moving steel, the drawer pack, or the knee well. On 72×24 Husky HOTL7202B12-class: drawers ~40" front; clips into one ~16" wood wing. Else wall or cart.

## Amazon pans

- NSF 18×13 6-pack (CURTA-class) if Prime
- Nordic Ware Naturals only after measuring rim (encapsulated steel ≠ bakery wire-in)

## Never-list

- Printed cages / dual towers / shop furniture
- Occupying the chair cave
- Hanging from sit/stand columns
- Explore renders of a large fixture before the buy-vs-print call
- CAD before pan-rim caliper **or** an explicit **buy**

## Handoff

Clips: `3d-print-design-brief` → DESIGN.md `product_class: bracket`, `expected_components` = clip count → `3d-print-openscad`. Buy: stop. No DESIGN.md required.
