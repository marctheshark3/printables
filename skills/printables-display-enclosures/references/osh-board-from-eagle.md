# OSH board case: parse before CAD

Use when enclosing a Crowd Supply / Soldered / Adafruit OSH board that ships a GitHub `.brd` + optional official STLs.

## Sequence

1. Official STL bbox (the printed case) — not the PCB.
2. Eagle `.brd`: layer-20 outline, `<element>` origins, package pads. Silk rev in the file may be older than the live board (Maker-Display GitHub = Display2 **v2.1**; Marc’s silk = **v2.2**). Tag `from-brd-vX.Y`.
3. Connector datasheets for Z only (2.54 mm female insulator **8.5 ± 0.15 mm**).

Never tell Marc “we have all the dimensions” from photos + marketing. That is a mule, not a first-print lock.

## Header that must stay

If the programming header is the OTA-fail serial poke: **blister + poke window**, not a uniform taller lid (USB/JST windows walk). Official Display2 Small Top is 7.6 mm and loses to 8.5 mm.

## Display2 numbers

See `references/maker-led-display2-envelope.md`.
