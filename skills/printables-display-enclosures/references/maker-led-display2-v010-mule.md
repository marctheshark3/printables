# Display2 case v0.1.0 mule (shipped)

Project: `~/Documents/the-grid/maker-led-display2-case`
Export: `VER=v0.1.0 bash scripts/export_stl.sh` → zip in `stl/`
DFM: HARD=0 both STLs (`--thin-fail-frac 0.35`). G-thin WARN = soft tessellation.

## Lock (do not re-litigate unless Marc reprints)

- Header **stays** — OTA-fail serial / CONNECT poke. Desolder is not a path.
- CAD origin: board centered; `cad = eagle − (52, 19.5)`.
- Outer **110.4 × 45.4**; cavity PCB+0.8 = **105.6 × 40.6**.
- Base Z **15.8** = floor 2.2 + seat 2.0 + pcb 1.6 + **10.0** above PCB (8.5 header + 1.5).
- Bezel face-on-bed, stop **+Z**. LED window **82 × 24** @ (−9.6, −6.66). Header poke **18 × 8** @ (40.8, 17.4).
- I/O in **base walls**: USB −X 13×8.5 @ y=11.3; switch +X 11×6 @ y=11.0; easyC/JST +Y 10×8.
- Posts **outside** PCB XY, Ø2.4 through. Brd holes are not M2.
- CONNECT/NOVA is **38 × 22** — not a lid-on bay. Pop the bezel to flash.
- Official 2019 Small Top 7.6 cannot close. Do not grow that lid as a uniform brick.
- First print is a mule. Live silk is v2.2; numbers are `from-brd-v2.1` + catalog Z.

Envelope + Eagle parse: `maker-led-display2-envelope.md`, `osh-board-from-eagle.md`.
