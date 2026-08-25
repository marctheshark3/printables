# Print orientation law (elevated trays / stands)

## Marc signal (2026-07-12)

**Print the top first** so the free end (feet) needs nothing under it. Design so geometry builds bottom-up on the printer from the top face.

## TOP-FIRST (default for elevated stands)

| Print Z | What |
|---------|------|
| **0 (bed)** | Rim **top** / highest use face after flip |
| **lip_h** | Pocket floor / hex seating plane |
| **→** | Walls, pillars, any structure grown from deck toward feet |
| **free end** | Feet + pad recesses (printed last) |

**Use:** flip so feet on desk, rim up, device into pocket.

### Implications

1. CAD in **print coordinates** when possible (Z=0 = bed face).  
2. Structure grows **from deck/rim toward feet** (supported base → free tip).  
3. Retention = **rim lips / tray depth from bed**, not free sphere nubs that would print into the bed.  
4. Do **not** auto-orient feet-down in slicer — ship as-exported; document in README.  
5. Supports off expected if pillars/walls are vertical or ≤45° from deck.

### Anti-patterns

- Feet-down print when Marc wants free end empty  
- Pin stilts “from bed” in use coords without flipping mental model  
- Domed nubs on seating plane when seating plane is on bed (into bed)

## Feet-down (legacy / explicit only)

Use only if Marc asks or part is a flat plate/bracket with no elevated free end.

## DESIGN.md must state

```
Print: TOP-FIRST | rim on bed | build toward feet
Use: flip | feet desk | pocket up
```
