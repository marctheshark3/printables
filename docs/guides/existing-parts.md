# Working from existing parts

[Documentation](../README.md) · [Design and validation](design-and-validation.md)

Start with an official drawing or vendor STEP when one is available. Photos and STLs need additional evidence before they can support a dimensioned part. Run the commands below from the repository root.

## Use a ChArUco photo

[`3d-print-photo-cad`](../../skills/3d-print-photo-cad/SKILL.md) recovers the scale of a printed board in a photo. Use it when a bought part has no drawing and the board is visible around it.

Print the board at 100%, then verify with a ruler that one square measures 15.0 mm:

```bash
python3 skills/3d-print-photo-cad/scripts/charuco_photo.py --board --out ./charuco
python3 skills/3d-print-photo-cad/scripts/charuco_photo.py photo.jpg --out ./charuco
```

`ok: true` means the board square recovered within 0.15 mm. `part_px_are_metric` remains false: the rectified PNG does not measure the part's lengths or hole diameters. A raised face is outside the metric board plane, and a top photo cannot supply thickness.

Part dimensions need a drawing or caliper evidence. The skill also supports an operator-asserted coplanar span when both endpoints lie on the paper. Label the resulting solid `photo-derived` and view it as one model in [the CAD inspector](inspection-and-instructions.md).

Real photos require OpenCV (`opencv-python`, including `cv2.aruco.CharucoDetector`) and numpy. Unit CI does not install them; missing OpenCV exits 2.

For a flat stencil or outline extrusion, use [`3d-print-image-silhouette`](../../skills/3d-print-image-silhouette/SKILL.md).

## Rebuild an STL as editable STEP

[`3d-print-reverse`](../../skills/3d-print-reverse/SKILL.md) reconstructs an existing STL with editable features and an analytic B-rep. Set `PROJECT` to the output project directory:

```bash
skills/3d-print-reverse/scripts/preverse run --stl in.stl --project "$PROJECT"
```

A successful result has:

- A valid `docs/PRINT_SPEC.yaml` and named parametric source.
- An analytic `step/<body>.step`.
- An STL from the rebuilt solid that passes `validate_project.py` with `HARD=0`.
- A `reports/<body>.deviation.json` whose measured deviation is within `max_deviation_mm`.

STEP export needs an OCC kernel through `VIBECAD_CMD`, a pinned `PREVERSE_STEP_IMAGE` digest, or the documented `PREVERSE_PYTHON` environment. Missing OCC exits 2 rather than writing a fake STEP. OpenSCAD and Blender cannot emit editable STEP. Analysis, IR work, and checks of committed reconstruction artifacts can run without OCC.

Triangle-wrapped STEP is refused. Fillet recovery is best-effort, and proof is mesh deviation against the input STL, not recovery of the original CAD design. See the [reconstruction method](../../skills/3d-print-reverse/references/reconstruction-method.md), [STEP kernel setup](../../skills/3d-print-reverse/references/step-kernel.md), and [reverse coupon example](../../examples/README.md).
