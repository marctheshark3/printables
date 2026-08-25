# Hex deck + bottom studs (desk platform class)

Product class used for DGX Spark stack exploration (`dgx-spark-stack` v3):

- Device sits **on top** of a soft-rim hex-perforated deck  
- **Studs hang under** the deck (elevation + optional nest)  
- Open under seating for bottom intake — studs only, not waffle under the chassis floor  

## TOP-FIRST print (required for elevated studs)

```
z=0 bed     = rim TOP face
z=rim_h     = deck TOP / seating
z=rim_h+t   = deck BOTTOM
then        = studs grow toward free tip
```

**DFM for free-end studs:**

- Wide root (`stud_root_d`) at deck with solid deck plug (no hex under stud)  
- ~45° shoulder hull root → mid diameter  
- Taper mid → tip  
- Soft tip chamfer  
- Supports off expected  

**Use orientation:** flip STL so studs on desk, pocket up. Slicer: import as-exported; do not auto-orient feet-down if model is TOP-FIRST.

## Multi-variant explore (A–E pattern)

When Marc asks for N versions of the same class:

1. One SCAD + `variant="A"|…`  
2. Export all, lineup + under stills, zip  
3. **Stop for pick** — do not crown all as print targets  
4. Converge = hybrid knobs only on the winner  

Variants that worked as a map:

| ID | Idea |
|----|------|
| A Sparse | large hex, 4 corner studs |
| B Dense | fine hex, 8 studs |
| C Dish | taller outer wall, fat studs |
| D Ring void | big center open + 6 hex studs |
| E Nest | stud pitch ↔ hex/cups for platform nest |

## Stack story still required

“Hex + studs” does not define stack path. Lock before marketing stack:

- under-tray only, or  
- interposer between chassis, or  
- platform under each unit only  

See `intent-lock-and-variants.md`.