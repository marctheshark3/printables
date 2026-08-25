# Soft geometry + FDM DFM (no 90° language)

Default when Marc says “designed for 3D printing”, soft edges, organic, or no sharp corners.
Built from DGX stand v1–v9 + FDM practice (Bambu P1S, 0.4 mm nozzle).

## Mindset

Design **for the process**, not CAD-pretty then hope:

1. **One fixed orientation** — elevated equipment default **TOP-FIRST** (see `print-orientation.md`). Document it.
2. **Overhangs ≤ 45°** (self-supporting). Prefer 45° chamfers/buttresses over horizontal shelves.
3. **No mid-air beams.** Anything that only appears mid-height over air = supports. Grow structure from the **print base** (rim/deck in TOP-FIRST) or split parts.
4. **Soft exterior language** by default when he asked for no 90° / smooth / organic.
5. **Feature sizes** multiples of **0.4 mm**; min solid feature ≥ **1.6 mm**.
6. **Product class first** — for bottom-vent equipment, open empty under beats “pretty stilts” (stand v6→v9).

## Soft / no-90° toolkit (OpenSCAD, no external libs)

| Goal | Pattern | Notes |
|------|---------|--------|
| Rounded plan | `offset(r=R) square([x-2R,y-2R],center=true)` | Fast, manifold-friendly |
| Exterior soft box | Extrude soft footprint; optional top/bottom chamfer via offset stack | Prefer over raw `cube` |
| Hex / circular openings | `circle($fn=6)` hex or high-$fn circle | **No square lattice holes** in soft mode |
| Capsule vents / windows | `hull()` two circles → extrude | Vertical slots preferred; side windows on open frames |
| Retention | Rim lips / tray depth from bed (TOP-FIRST); or cylindrical nubs only if not into bed | Not square L-lips |
| Edge soften (visible) | Bed chamfer 0.8–1.6 mm; foot chamfer on free end | Reduces elephant-foot + sharp feel |
| Joint strength | Fillet external corners; avoid knife-edge Z-notches | FDM layer notch strength |

### Fillet / chamfer reality in OpenSCAD 2021.01

Native `fillet()` does **not** exist. Practical options ranked for **Docker reliability**:

1. **Design soft from the start** (offset footprints, hull, 45° language) — preferred.
2. **2D offset rounding** then extrude (plan fillets).
3. **Hull of spheres/cylinders** for local rounds (slow if abused).
4. **Minkowski with sphere** — easy global soft but **slow**, grows dims (compensate), explodes CGAL on complex models. Use only on small sub-modules.
5. Optional later: vendor **BOSL2** / **Round-Anything** into project `lib/` and mount in Docker. Do not block a job on missing host libs.

Helper modules live in `templates/soft_helpers.scad` — copy into project or `include` via relative path if you copy the file into `src/lib/`.

## DFM rules (FDM / P1S) — required

1. **Orientation documented.** Elevated equipment → **TOP-FIRST** unless Marc forces feet-down.
2. Overhangs ≤ 45°. Bridges free-span ≲ ~10–12 mm only when midspan fill is intentional.
3. **Equipment bases:** open frame empty under seating (see `understructure-aesthetics.md`). Do **not** default to pin stilts.
4. When midspan fill is required (solid tray, not DGX-class): soft waffle, unique grid, 8 soft buttresses + edge beam — never pin forest.
5. Unique stilt grid only if stilts are used (dedup). Overlapping stilts → non-manifold (`Simple: no`). **Stilts are aesthetic reject under equipment.**
6. Open I/O faces; don’t seal ports with walls.
7. Walls/ribs: 1.6 / 2.0 / 2.4 / 3.2 mm family.
8. Report **STL volume (cm³)** with every redesign. “Minimal plastic” overrides heavy cell fills.

## Plastic budget (measure it)

| Approach | Plastic | When |
|----------|---------|------|
| Open frame empty under + perimeter pillars | **low** | **Default DGX / bottom-vent gear** (stand v9 ~163 cm³) |
| Soft waffle midspan | med–high | Only if open frame hammocks and product needs floor |
| Pin stilts | low–med | FDM-valid, **Marc aesthetic reject** |
| Full vertical cells | often ~2× | Only if max stiffness requested |
| Mid-air X-brace | low plastic, **bad FDM** | Reject unless split parts |

## Soft-mode rejection checklist

Fail the design if:

- [ ] Visible raw cube corners when soft mode requested
- [ ] Square-only lattice as the visual language
- [ ] Mid-air X-braces / floating cross-members
- [ ] Overhangs > 45° without intentional supports note
- [ ] Non-manifold (`Simple: no`)
- [ ] Volume not reported vs prior version
- [ ] Pin forest under seating deck for equipment
- [ ] Waffle under bottom-vent equipment without explicit ask
