# FDM craft for Blender printables (OpenSCAD lessons applied)

## Laws (non-negotiable)

1. **Intent first** — DESIGN.md with product_class + print_orientation + backend/scaffold.
2. **Hybrid is default for multi-body cases** — OpenSCAD owns **mechanical shells** (base/tray/ports/bosses); Blender owns **organic/hex lids** only when needed.
3. **Geometry is the design** — never “fix” mechanical shells with voxel remesh.
4. **Dimensional ports = from-spec** — never photo-guess Pi/port pitches.
5. **Look before ship** — separate stills per printable body; vision or human OK.
6. **DFM gate HARD=0** — necessary, not sufficient (PASS ≠ pretty).
7. **OpenSCAD dimensional default** for stands/brackets/frames/ported bases.

## Hybrid ship pattern (locked 2026-08)

Proven on Pi Zero noloop:

| Half | Backend | Why |
|------|---------|-----|
| Base / tray / ports / bosses | **OpenSCAD** | Clean booleans, soft shells, DFM-stable |
| Lattice / hex / Voronoi lid | **Blender** *or* OpenSCAD Voronoi | Blender: **solid plate + ONE joined cutter** only |
| Full dimensional product | OpenSCAD alone | Prefer when no organic skin |

**Gold print pack:** `~/Documents/the-grid/rpi-zero-print-noloop`  
- Base = honeycomb OpenSCAD `enable_keyring=false`  
- Lid = Blender hex plate (`rpi-zero-voronoi-noloop` v0.5+)

**Do not** re-fight pure-Blender ported bases unless Marc explicitly wants Blender-only R&D.

## Blender lid craft (only good path)

1. Solid rounded plate (not capsule soup)
2. Build **all** hex/Voronoi cell cutters into **one** mesh
3. **Single** boolean DIFFERENCE (`FAST` solver OK)
4. Union corner pads + pins under pads only
5. Optional lip rim
6. `cleanup_fdm(..., mode="light")` — never voxel+fatten shell

**Banned:** N sequential cell booleans · capsule ridge unions · voxel remesh on mechanical · assembly-only preview.

## cleanup_fdm modes

| mode | When | Never |
|------|------|-------|
| `light` (default) | everything mechanical + finished lids | — |
| `voxel` | rare organic soup submesh only | outer walls, ports, bosses |

## Backend routing

| Job | Backend |
|-----|---------|
| Stand, bracket, open-frame, PIP hinge | OpenSCAD only |
| Ported enclosure **base** | OpenSCAD only |
| Hex / honeycomb / true Voronoi **lid** | Blender (joined cutter) **or** OpenSCAD Voronoi |
| Full case photo twin | Hybrid pack (SCAD base + lattice lid) |
| Viewport demo / rocket toy | blender-mcp explore — not print until gated |

## Reliability loop

```
brief → backend pick (hybrid OK) → scaffold each half → build
  → separate stills → vision → gate each STL → one zip pack
```

## vs online MCP demos

Demos = viewport beauty. Us = Bambu FDM. MCP optional explore; ship via OpenSCAD export and/or `pblend`.
