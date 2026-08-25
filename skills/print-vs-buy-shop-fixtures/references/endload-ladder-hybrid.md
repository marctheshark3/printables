# End-load ladder hybrid (v4)

Gold: `~/Documents/the-grid/husky-sheet-pan-rack/`
Use after the user rejects buying a bun cart and wants wood + printed joints.

## Architecture

Copy the commercial countertop end-load rack: two 1×2 **ladders**, pans slide on the **rungs**, open front, rear stop. Not diagonal posts. Not a PETG cage. Never print pans or wheels.

## Joint

Printed U at each rung/post crossing. Flange on bed, open U, no bridges. #8 into **post and rung**. Pan sits on the 1×2 (ledge analog). Front STL open; rear STL has a stop lip.

If a still shows the printed part on the pan and not on the wood, form-reject. Ship a 2D slice, not an isometric that reads as “diagonal.”

## Hybrid print BOM (PETG, P1S)

- 6× rung_joint + 6× rung_joint_stop
- 8× corner_gusset
- 4× caster_shoe (print one first)
- 1× spacing_jig

Cut (assume 19×38 mm S4S — measure): 4 posts 22 in, 6 rungs 18 in, 4 width ~13 1/8 in set from the real pan.

Electronics: 3 trays / ~120 mm pitch. Same joints scale to 7 bakery slots.

Prototype 10 lb/tray, 35 lb total — not NSF.

## Optional all-print stock

`post_segment` 180 mm and `rung_segment` 220 mm, Ø8 peg / +0.6 mm socket. P1S cannot print 18 in bars. Still buy pans. Hybrid is the Home Depot build.

## Deliver

Gated STL zip + slice/plan/front/BOM views + hardware-store cut list. Discord `#stl-design`: paths first.
