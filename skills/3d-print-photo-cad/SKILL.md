---
name: 3d-print-photo-cad
description: Scale a photo with a ChArUco board. Not a caliper.
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

A photo is not a caliper. The script recovers the board scale. It does not measure the part. The homography is the board plane. Vision may name a tab or a hole. It may not assign a length.

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
4. Run the measure script. `ok: true` means the board square recovered within **0.15** mm. It does not mean the part was measured. `part_px_are_metric` is false. Do not read lengths or hole diameters off the rectified PNG.
5. Part millimetres come from a drawing or a caliper. The only length this script can emit is `--coplanar-span x1,y1,x2,y2` in original-photo pixels, and only when both points lie on the paper. That span is operator-asserted, not verified. Do not mark a raised face.
6. A top photo is **XY only** for an edge on the paper. Thickness is not in that photo. Do not invent Z.
7. VibeCAD parameters are a drawing, a caliper, or that asserted span (`3d-print-vibecad`). Inspector entry is one model (`3d-print-cad-render`).
8. Do not cut a hole from this photo. A hole diameter needs a drawing or a caliper.

## How to Run

OpenCV (`opencv-python`, `cv2.aruco.CharucoDetector`) and numpy are required for a real photo. Unit CI does not install them. Missing OpenCV exits 2.

```bash
python3 skills/3d-print-photo-cad/scripts/charuco_photo.py --board --out ./charuco
python3 skills/3d-print-photo-cad/scripts/charuco_photo.py photo.jpg --out ./charuco
python3 skills/3d-print-photo-cad/scripts/charuco_photo.py photo.jpg --out ./charuco --coplanar-span 100,200,180,200
```

`--board` writes `charuco-15mm.png` and `print.html`. Measure writes `<stem>-board-plane.png` at 10 px/mm and `<stem>-measure.json`.

## Pitfalls

- Reading millimetres off a vision description
- Fit-to-page, or trusting the PNG without the ruler check
- Calling a product-page box or a community STEP the model
- A side or raised face marked as `--coplanar-span`, or measured off the rectified PNG. It reads large. The script does not verify coplanarity.
- Dark-blob or line guesses on the checkerboard. An overlay has to sit on the plastic before a length is real
- A hole without a measured diameter

## Verification

- [ ] Printed square ruler-checked at 15.0 mm
- [ ] measure json `ok: true` is the board check only; `part_px_are_metric` is false
- [ ] No part millimetre was read off the rectified PNG
- [ ] A span, if present, is `coplanar_asserted` and both points were on the paper
- [ ] Catalog / PRINT_SPEC says `photo-derived` for photo dims
- [ ] No hole without a measured diameter
- [ ] Inspector shows one model
