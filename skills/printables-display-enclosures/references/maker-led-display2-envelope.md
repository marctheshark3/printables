# Maker Display2 enclosure envelope

Source: SolderedElectronics/Maker-Display `Maker Display2/Maker Display2.brd` (Eagle 7.3). Silk in file: **Maker Display2 v2.1**. Marc’s live board silk: **v2.2**. Tag CAD `from-brd-v2.1` until calipers confirm.

Official 3D kit (same repo zip, 2019) already lives at `~/Documents/the-grid/maker-led-display/printables/official/`.

## PCB (origin bottom-left, mm)

- Outline **104.000 × 39.000**. Left-edge USB notch Y 28–34 (1 mm chamfer).
- Programming header `ESP-PROGRAMMING-PORT` U$3 @ **(92.8, 36.9)** — 1×6, 2.54 pitch, pads X **86.45–99.15**, near top-right long edge. Body silk 15.24 × 2.54.
- Micro-USB `U-F-M5DD-Y-L` U$15 @ **(5.6, 30.8) R90** — faces **left short edge**.
- easyC = `J3` `1X04_1MM_RA` @ **(12.1, 34) R180** (same corner as USB). Logo-only `EASYC` package is not the connector.
- Battery JST-2-SMD JP1 @ **(45, 33) R270** mid-top.
- Slide switch SK-12D02 S1 @ **(101.4, 30.5) R90** right short edge.
- ESP-12 X1 @ **(92.8, 14.0)** ~16×24. GPIO are edge pads at x=101.5, not a second header.
- Plain holes Ø0.6 / Ø1.2 — **not M2**. Official case posts sit **outside** the PCB (case 108 × 55.4).

## Official Small case STL bbox (already printed)

- Top 108.0 × 55.4 × **7.6**
- Bottom 108.0 × 55.4 × **12.6** (LiPo well)
- Assembled ~20 mm + legs

## Header Z (datasheet, not calipers)

- Standard 2.54 mm female insulator **8.5 ± 0.15 mm** (Adafruit F201 / industry). Official top 7.6 cannot close.
- Lid cavity at header ≥ **10 mm** above PCB + poke window ~**18 × 8** if NOVA/CP2102 must mate with lid on.
- Keep header: last-resort serial when OTA (`rage-matrix.local`) fails. Do not recommend desolder as the path.

## Vendor marketing (cross-check only)

- Crowd Supply / Soldered: Display2 **104 × 39–39.5 × 7.2** overall slab (LEDs + PCB). Matches .brd XY.

## Case redesign lock (option 3)

Snug two-piece: shallow back, XY ≈ PCB + 0.8, LED bezel, USB/easyC/JST/switch on the edges above, header blister + poke hole. First print = mule. One useful caliper: header plastic top → PCB.
