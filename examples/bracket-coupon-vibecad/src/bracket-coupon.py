"""Printable L-bracket coupon. VibeScript / Part CSG for 10-X-eng/vibecad.

Named millimetre parameters match docs/PRINT_SPEC.yaml.
Runs inside VibeCADCmd/freecadcmd or POST /v1/run. Host python3 has no FreeCAD.
"""
from pathlib import Path

# Named millimetre parameters (PRINT_SPEC.yaml dimensions).
object_x = 40.0
object_y = 30.0
object_z = 12.0
flange = 12.0
hole_d = 4.2

hole_inset = 7.0


def project_root():
    from pathlib import Path

    return Path(__file__).resolve().parent.parent


def build_solid():
    """L as two overlapping boxes fused to one solid, then holes cut."""
    import FreeCAD as App
    import Part

    arm_x = Part.makeBox(float(object_x), float(flange), float(object_z))
    arm_y = Part.makeBox(float(flange), float(object_y), float(object_z))
    # Overlapping arms must become one solid. Remaining N shells is HARD.
    fused = arm_x.fuse(arm_y).removeSplitter()
    if len(fused.Solids) != 1:
        raise RuntimeError(
            f"HARD: fuse left {len(fused.Solids)} solids; expected_shells is 1"
        )

    z_hat = App.Vector(0, 0, 1)
    cylinders = [
        Part.makeCylinder(
            float(hole_d) / 2.0,
            float(object_z) + 2.0,
            App.Vector(14.0, float(flange) / 2.0, -1.0),
            z_hat,
        ),
        Part.makeCylinder(
            float(hole_d) / 2.0,
            float(object_z) + 2.0,
            App.Vector(float(object_x) - hole_inset, float(flange) / 2.0, -1.0),
            z_hat,
        ),
        Part.makeCylinder(
            float(hole_d) / 2.0,
            float(object_z) + 2.0,
            App.Vector(float(flange) / 2.0, float(object_y) - hole_inset, -1.0),
            z_hat,
        ),
    ]
    cutters = cylinders[0].fuse(cylinders[1]).fuse(cylinders[2])
    body = fused.cut(cutters)
    if len(body.Solids) != 1:
        raise RuntimeError(
            f"HARD: cut left {len(body.Solids)} solids; expected_shells is 1"
        )
    return body


def _feature(doc_name):
    import FreeCAD as App

    doc = App.newDocument(doc_name)
    feat = doc.addObject("Part::Feature", "bracket")
    feat.Shape = build_solid()
    doc.recompute()
    if len(feat.Shape.Solids) != 1:
        raise RuntimeError(
            f"HARD: document solid count {len(feat.Shape.Solids)} != expected_shells 1"
        )
    return feat


def export_binary_stl(path):
    import Mesh

    feat = _feature("bracket_coupon")
    Mesh.export([feat], str(path))


def export_step(path):
    import Part

    feat = _feature("bracket_coupon_step")
    path.parent.mkdir(parents=True, exist_ok=True)
    Part.export([feat], str(path))


def main():
    try:
        import FreeCAD  # noqa: F401
        import Mesh  # noqa: F401
        import Part  # noqa: F401
    except ImportError:
        raise SystemExit(
            "HARD: host python3 has no FreeCAD. Execute inside VibeCADCmd/"
            "freecadcmd (x86_64 AppImage) or POST /v1/run. Linux ARM "
            "qemu-x86_64 AppImage is not a supported backend."
        ) from None

    import os
    from pathlib import Path

    root = project_root()
    out = Path(os.environ.get("PRINTABLES_STL", str(root / "stl" / "bracket-coupon.stl")))
    out.parent.mkdir(parents=True, exist_ok=True)
    export_binary_stl(out)
    print(f"exported {out}")
    step = Path(os.environ.get("PRINTABLES_STEP", str(root / "step" / "bracket-coupon.step")))
    export_step(step)
    print(f"exported {step}")


# FreeCADCmd execs this file with __name__ == stem, not __main__.
if __name__ in {"__main__", Path(__file__).stem}:
    main()
