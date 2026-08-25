# Print-in-place (PIP) design patterns

Two families:

1. **Structure PIP** — elevated support grown from print base (orientation-aware).
2. **Mechanism PIP** — hinges/lids that free after print.

## Clearances (Bambu P1S start)

| Fit | Gap (mm) | Use |
|-----|----------|-----|
| Press | 0.05–0.10 | Tight pins |
| Slip | **0.20** | Drop-in pockets |
| Free hinge | **0.30–0.50** diametral | PIP hinges |
| First-try hinge | **0.40** + 0.20 axial | Avoid fuse |

Parametrize `pip_gap` / `print_slop`. Expose for `-D` re-export.

## Structure PIP — elevated

**Respect product class** (see `understructure-aesthetics.md`):

### Equipment open frame (DGX default)

- Seating surface only (hex/pocket)
- **Empty** under-volume
- Perimeter pillars from deck → feet (TOP-FIRST: grow from deck underside toward free feet)
- Optional windowed skirt; open rear
- Thin edge beam under deck **perimeter only**

### When midspan fill is required

1. Soft waffle under-ribs (readable)
2. Soft buttresses (8)
3. Under-ring
4. **Not** pin forest

**Pin stilts:** FDM-valid, Marc aesthetic reject. `stilts_enable=false` default.

**Never:** mid-air X-braces; pin forest as visual primary; waffle under equipment that needs empty airflow; volume swap without reporting cm³.

### Orientation

With **TOP-FIRST** (`print-orientation.md`): structure attaches to deck and grows toward feet free end — not “stilts from desk bed.”

## Mechanism PIP

Knuckle/pin, interlocking cone (`templates/pip_hinge_cones.scad`), living hinge, or snap-together.
Checklist: single `pip_gap`, no zero-gap faces, orientation fixed, first-layer fusion mitigated.

## Docker

Pure OpenSCAD or vendored `src/lib/`. Hermetic export preferred.
