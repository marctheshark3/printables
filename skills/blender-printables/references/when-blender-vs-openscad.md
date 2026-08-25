# When Blender vs OpenSCAD (hybrid locked)

| Prefer **OpenSCAD** | Prefer **Blender** | Prefer **hybrid** |
|---------------------|--------------------|-------------------|
| Stands, brackets, open frames | True organic / hex **lid only** | Ported base + lattice lid |
| Ported trays / bases | Joined-cutter honeycomb plate | Pi Zero style cases |
| Screw bosses, hole grids | Complex boolean skins (still light cleanup) | Photo twin enclosures |
| PIP hinges, dimensional SoT | — | — |

## Bundle entry

- `/printables` → OpenSCAD path (default)
- `/printables-blender` → Blender lid / organic half only, or full hybrid orchestration
- Hybrid ship: both backends, **one** DESIGN.md story, **one** zip

## Gold

- Print pack: `~/Documents/the-grid/rpi-zero-print-noloop`
- OpenSCAD case SoT: `~/Documents/the-grid/rpi-zero-honeycomb-case` (`enable_keyring`)
- Blender lid SoT: `~/Documents/the-grid/rpi-zero-voronoi-noloop` (hex plate v0.5+)

## Never

- Pure Blender ported base as default
- Capsule-ridge Voronoi lids
- Voxel melt cleanup on shells
- Claiming done without separate stills
