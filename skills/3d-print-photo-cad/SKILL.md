---
name: 3d-print-photo-cad
description: Measure a part from a ChArUco photo. Not a caliper.
version: 1.0.0
author: Marc Mailloux, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [charuco, metrology, ruler, photo-derived]
    related_skills: [3d-print-design-brief, 3d-print-vibecad, 3d-print-cad-render, 3d-print-validate]
---

# Photo to CAD

A photo is not a caliper. Millimetres come from a printed **15.0 mm** ChArUco board, after a ruler check, then `scripts/charuco_photo.py`. Vision may name a tab or a hole. It may not assign a length.

Label the solid `photo-derived`. Do not mill from it. Do not cut a hole whose diameter was not measured.

## When to Use

- Bought part has no vendor drawing, and it has to be modeled in millimetres
- "model this from a photo" with a scale board in the frame
- Official drawing or vendor STEP exists — use that and skip this skill

**Don't use for:** a flat outline extrusion, a mesh scan, or any length read off an unscaled picture.

## Flow

1. Name the part. If an official mechanical drawing exists, use it. Skip the board.
2. No drawing? Print the board at **100%**. No fit-to-page. One square must measure **15.0 mm** with a ruler. Markers do not encode size.
3. Part in the middle, board visible on all four sides.
4. Run the measure script. Exit 0 and `"ok": true` before any CAD number is written. Corners must be at least 12. `recovered_square_mm` must be within **0.15** of 15.0. Else stop.
5. On the rectified PNG, pixel distance / 10 = mm. Cite the json. Provenance `measured`. Source `photo-derived`.
6. A top photo is **XY only**. Thickness is a second photo of the part on its side on the same board, a drawing, or a caliper. Do not invent Z.
7. VibeCAD parameters are those numbers only (`3d-print-vibecad`). Inspector entry is one model (`3d-print-cad-render`).
8. Cut a hole only if its diameter was measured on the rectified image, or it is on a drawing. No other holes.

## How to Run

OpenCV (`opencv-python`, `cv2.aruco.CharucoDetector`) and numpy are required for a real photo. Unit CI does not install them. Missing OpenCV exits 2.

```bash
python3 skills/3d-print-photo-cad/scripts/charuco_photo.py --board --out ./charuco
python3 skills/3d-print-photo-cad/scripts/charuco_photo.py photo.jpg --out ./charuco
```

`--board` writes `charuco-15mm.png` and `print.html`. Measure writes `<stem>-board-plane.png` at 10 px/mm and `<stem>-measure.json`.

## Pitfalls

- Reading millimetres off a vision description
- Fit-to-page, or trusting the PNG without the ruler check
- Calling a product-page box or a community STEP the model
- A side or raised face used as the scale check
- Dark-blob or line guesses on the checkerboard. An overlay has to sit on the plastic before a length is real
- A hole without a measured diameter

## Verification

- [ ] Printed square ruler-checked at 15.0 mm
- [ ] measure json `ok: true`, corners ≥ 12, recovered square within 0.15 mm
- [ ] Every CAD mm cites that json, a drawing, or a caliper reading
- [ ] Catalog / PRINT_SPEC says `photo-derived` for photo dims
- [ ] No hole without a measured diameter
- [ ] Inspector shows one model
