# VibeCAD host instruction (in-app Grok)

Public, path-free sequence for the 10-X-eng/vibecad in-app Assistant. This pack does not vendor VibeCAD. This is not the PyPI package named vibecad.

1. Write `docs/PRINT_SPEC.yaml` first (`3d-print-design-brief`). Validate it. Chat, the 3D view, `.FCStd`, MJCF, and `DESIGN.md` cannot override it.
2. Set `cad.backend: vibecad` and `cad.parametric: true` only when remaking in VibeCAD. Source files must be project-relative Python/VibeScript with `identifier =` for every PRINT_SPEC dimension. `.FCStd` or Markdown alone is not a source.
3. Build with VibeScript / Part CSG. Booleans must yield the declared `expected_shells`. A `multiFuse` that remains N shells is a HARD fail, not a preview pass.
4. Export a binary STL inside VibeCAD. One STL per independently manufactured body. A VibeCAD preview is not printable.
5. From this printables checkout, run `skills/3d-print-validate/scripts/validate_project.py` on the project (and `validate_assembly.py` if `assembly` is present). HARD=0 is required.
6. If VibeCAD is down, OpenSCAD remains the dimensional default (`3d-print-openscad`). Do not invent a kernel fallback inside VibeCAD.

Do not enable VibeCAD MCP (it disables this Assistant). Sign-in stays in VibeCAD Preferences; never type passwords or device codes into chat. Geometry runs in VibeCADCmd/freecadcmd or `POST /v1/run` — host python3 has no FreeCAD. Supported backend: x86_64 AppImage / freecadcmd only.
