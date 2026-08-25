# Hybrid half-sheet project cart

Use when commercial bun racks are too expensive but the user still wants the rack/cart form.

## Functional reference

Commercial half-height rack pattern:
- four corner posts;
- open front/back, end-loaded pans;
- paired side ledges;
- top and bottom perimeter frames;
- four casters, at least two locking;
- commercial half sheet: nominal 13 × 18 in (330 × 457 mm), with brand variation at the rolled rim.

For electronics projects, three levels at roughly 120 mm pitch are more useful than copying ten 3-inch bakery levels.

## Default architecture

Do **not** print long structural beams merely to claim the cart is fully printed. Preserve the commercial architecture with a hybrid build:

- 1×2 lumber, aluminum angle, EMT, or other straight shop stock for four posts and perimeter members;
- printed pan-slide clips, corner gussets, caster interfaces, and assembly jigs;
- a fourth half sheet or plywood as the top deck;
- casters as purchased hardware, never printed wheels.

This is a one-for-one **functional** copy, not a cosmetic extrusion replica. It avoids bed-limited beam segmentation, multi-kilogram filament use, and creep-prone structural joints.

## Prototype sizing for three half sheets

Starting envelope, to be reconciled against the actual pan and stock:
- clear pan span: about 334 mm, set with the real pan during assembly;
- frame depth: about 495 mm;
- wood-frame height: about 560 mm;
- total height on 2-inch casters: about 620 mm;
- ledge elevations: 115, 235, and 355 mm;
- target working load: 10 lb per tray / 35 lb total until progressively load-tested; never inherit a commercial rack's rating.

## Minimal printable BOM

- 12 pan-slide clips: two per side per tray, broad ledge rather than a captured precision channel;
- 8 corner gussets;
- 4 caster shoes/plates customized to measured caster hardware;
- 1 spacing jig.

Use PETG. Keep aluminum electrically isolated from bare PCB undersides with mats or standoffs. No loose LiPo directly on a conductive tray.

## Measurement gates

Before production:
1. Measure one actual pan's outside rim width/depth.
2. Measure actual structural stock section.
3. Measure caster plate/stem interface.
4. Build width around the real pan with ~2 mm total lateral play.
5. Progressively load-test on locked casters.

An oversized support ledge can be non-precision; a captured rim channel or caster socket is a critical fit and cannot ship from assumed dimensions.
