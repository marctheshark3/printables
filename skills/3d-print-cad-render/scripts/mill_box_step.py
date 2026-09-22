"""Export a 20×12×8 mm box STEP for inspector live tests. FreeCADCmd -c only."""
import os
import sys

def main() -> int:
    out = os.environ.get("CAD_RENDER_STEP")
    if not out:
        sys.stderr.write("CAD_RENDER_STEP required\n")
        return 1
    import Part
    box = Part.makeBox(20, 12, 8)
    box.exportStep(out)
    sys.stderr.write(f"wrote {out} vol={box.Volume}\n")
    return 0

raise SystemExit(main())
