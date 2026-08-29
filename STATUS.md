# Status

Last reviewed 2026-08-28.

## Supported path

- `docs/PRINT_SPEC.yaml` is the only machine source of truth. DESIGN.md is never parsed.
- An assembly is multiple independently manufactured bodies in `geometry.stl_files`.
- OpenSCAD is the default for dimensional mechanical parts.
- Blender is allowed only for organic or lattice bodies.
- VibeCAD (10-X-eng/vibecad) is an optional x86_64 backend (`cad.backend: vibecad`) using the same validators; it is not the default kernel and is not required by `/3d-print`.
- Hybrid means separate declared bodies owned by separate backends—not two kernels editing one body.
- `3d-print-validate` is backend-neutral and mandatory after every export.
- `3d-print-robotics` is the class skill for numbered `robot-module` kit bodies.
- `3d-print-sim` / `validate_assembly.py` is the assembled occupancy gate when `assembly` is present. A render is not proof.
- `3d-print-reverse` rebuilds an existing STL as editable analytic STEP plus a gated STL. Reverse needs OCC (10-X-eng/vibecad or CadQuery). OpenSCAD and Blender cannot satisfy STEP.
- `3d-print-pack` and `3d-print-slice` are optional manufacturing extras (zip + process card). They are not in `/3d-print`. Printer upload is `bambu-mcp`.
- `sim2real: true` is a PRINT_SPEC claim gated by mass/friction/actuator coupons (measured or datasheet). Assumed calibration cannot claim it.
- HARD failure means the part is not deliverable.

## Enforced today

- parametric backend declaration
- named CAD parameter for every critical dimension
- units, tolerance, and provenance
- one declared STL per printable body
- overlapping exported solids forbidden
- watertight boundary and non-manifold checks
- face-orientation and duplicate-face checks
- expected connected-shell count
- positive volume and X/Y/Z build envelope
- fit evidence, service material, and drainage policy
- explicit print orientation and supports policy
- sampled mesh thickness vs `geometry.min_wall_mm`
- assembled occupancy, joint sweep, and hub section check when `assembly` is present
- sim2real claim requires measured or datasheet mass, friction, and actuator coupons

## Known limits

- Thickness audit is sampled inward-ray, not an exact-kernel wall proof. HARD uses `thin_wall_area_frac=0.02` and 0.05 mm tessellation slack.
- Pack zip is not a slicer project unless `3d-print-slice` ran.
- 3MF emission needs a local slicer CLI; CI does not ship one. Missing slicer prints `SKIP: no slicer CLI` and writes no fake 3MF.
- Live Bambu control is the sibling `bambu-mcp` repo. This pack never stores printer secrets (access code, serial, LAN IP).
- Split-for-bed is an explicit repair of envelope HARD, not automatic. It declares two STLs and does not scale the part.
- Coarse overhang analysis is conservative and can warn on intentional geometry.
- Self-intersection detection is not a full exact-kernel proof; each CAD backend must validate its final solid before export.
- Assembled occupancy is in-process mesh placement plus a handbook hub-section check, not FEA.
- The installer is additive. It does not remove old user-local skill directories.
- Blender still depends on Blender's boolean and modifier behavior; malformed output must fail the shared validator.
- VibeCAD on Linux ARM qemu-x86_64 AppImage is not a supported backend. Boolean welding of overlapping solids remains a known limit until a live coupon exports one solid through VibeCADCmd/freecadcmd.
- Reverse engineering needs OCC. OpenSCAD and Blender cannot emit editable STEP. 10-X-eng/vibecad `mesh.to_shape` is faceted, not parametric; reconstruction is a separate modeling task (fork `mesh.reconstruct_parametric` upstream). Default CI does not invoke VibeCAD, CadQuery, Docker, or OCC. ARM qemu-x86_64 AppImage is unsupported. v1 feature vocab is prismatic FDM; organic scans may only reach `analytic`/`organic`. Proof is mesh deviation vs the input STL, not “this was the original CAD.” Fillet recovery is best-effort. Short STL chords stay warning-only.

## Removed

- The old `printables-*`, `openscad-printables`, `blender-printables`, and `vibecad-printables` names were removed from this repository.
- Private project notes, machine-specific paths, and unused house regression prose were removed from the public skill tree.

There is no compatibility promise for code that does not satisfy the current contract. Working artifacts stay; broken artifacts become negative regression fixtures or leave the pack.
