# Status

Last reviewed 2026-08-26.

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
- assembled occupancy, joint sweep, and hub section check when `assembly` is present
- sim2real claim requires measured or datasheet mass, friction, and actuator coupons

## Known limits

- STL geometry cannot prove wall thickness; the contract and slicer own that measurement.
- Coarse overhang analysis is conservative and can warn on intentional geometry.
- Self-intersection detection is not a full exact-kernel proof; each CAD backend must validate its final solid before export.
- Assembled occupancy is in-process mesh placement plus a handbook hub-section check, not FEA.
- The installer is additive. It does not remove old user-local skill directories.
- Blender still depends on Blender's boolean and modifier behavior; malformed output must fail the shared validator.
- VibeCAD on Linux ARM qemu-x86_64 AppImage is not a supported backend. Boolean welding of overlapping solids remains a known limit until a live coupon exports one solid through VibeCADCmd/freecadcmd.

## Removed

- The old `printables-*`, `openscad-printables`, `blender-printables`, and `vibecad-printables` names were removed from this repository.
- Private project notes, machine-specific paths, and unused house regression prose were removed from the public skill tree.

There is no compatibility promise for code that does not satisfy the current contract. Working artifacts stay; broken artifacts become negative regression fixtures or leave the pack.
