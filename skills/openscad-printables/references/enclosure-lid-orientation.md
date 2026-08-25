# Enclosure lid print orientation

Proved 2026-08-23 on `~/Documents/the-grid/vigil-sense-solar-sled/` lid.

## Law

A tray lid with an inner fence that is **smaller than the cap** cannot print fence-on-bed. The cap brim is a 90° hang → `dfm_gate` **G-overhang HARD** (~34% unsupported on that lid).

**Print:** cap on bed (Z=0), fence extruded **+Z**.  
**Use:** flip so the fence drops into the sled. Set DESIGN `use_flip: lid-only`.

Same family as display bezel: face/cap on bed; plug/fence +Z (`references/display-enclosure-bezel.md`).

## Export

`expected_components: 1` **per STL**. `dfm_gate.py` does **not** accept `--expected-components` — it reads DESIGN.md. Export `which=` shells separately; never gate an assembly mesh.
