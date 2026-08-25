# Display enclosure bezel + tray

Companion to blender-printables `references/display-desk-case.md` (routing). **CAD lives here.**

## Bezel print orientation (hard lesson)

```
z=0     → outer face on bed
z=bezel_t → start of plug rim
z=bezel_t+rim → plug top seats into base cavity
```

If plug is built at **negative Z** under the face, DFM G-overhang HARD and the part is wrong for feet-down.

## Soft G-thin

Rounded `soft_rect` / soft_box STLs often show 20–30% edges < 0.5 mm from **chord tessellation**, not knife walls. With `soft_mode: yes` or `--thin-fail-frac 0.35`, WARN is OK if walls ≥ 1.6 mm by design and stills look solid.

## I/O

Mark USB/STEMMA/SD/button as assumed until fit-check. Do not invent M2.5 pitch without measurement or drawing.

## Gold

`~/Documents/the-grid/pyportal-desk-case`
