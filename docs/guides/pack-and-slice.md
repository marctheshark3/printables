# Pack and slice

[Documentation](../README.md) · [Design and validation](design-and-validation.md)

After project validation reports `HARD=0` and any declared assembly passes its gate, package the project and write process cards. Run these commands from the repository root with `PROJECT` set to the exported project's directory.

## Package the project

```bash
python3 skills/3d-print-pack/scripts/pack_project.py "$PROJECT"
```

[`3d-print-pack`](../../skills/3d-print-pack/SKILL.md) writes `pack/<part>.zip` containing the spec, CAD source, STLs, generated `docs/PRINT_NOTES.md`, and `MANIFEST.sha256`. Optional STEP files and render stills are included when present. The packer refuses a project that fails validation.

Print notes come from the spec: orientation, bed face, supports, material, nozzle, and layer height. The zip is a deliverable archive; slicer output is generated separately.

## Prepare slicer output

```bash
python3 skills/3d-print-slice/scripts/slice_project.py "$PROJECT"
```

[`3d-print-slice`](../../skills/3d-print-slice/SKILL.md) writes `slice/<body>.process.json` from `PRINT_SPEC.yaml`. A process card records the printer profile, build volume, nozzle, layer height, material, orientation, supports policy, and STL path.

A 3MF is emitted only when a slicer CLI is configured through `ORCA_SLICER`, `BAMBU_STUDIO`, or `PRUSA_SLICER`. With none configured, the command prints `SKIP: no slicer CLI`, keeps the process card, and writes no fake 3MF. Unit CI needs no slicer.

## Hand off to a printer

Inspect the part in print orientation and inspect the slicer output. A validated STL is not permission to print.

Live printer upload and control belong to the sibling `bambu-mcp` repository. Printables stores printer profiles and build volumes, while printer identities, access codes, serials, and LAN IPs stay outside this pack. See [security guidance](../../SECURITY.md).
