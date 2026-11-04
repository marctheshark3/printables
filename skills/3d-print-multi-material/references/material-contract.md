# Optional material contract

`schema_version: 1` retains its existing manufacturing material and composite
bodies. The optional `multi_material` block adds logical filaments and domains.
Old specifications omit it and keep the original path.

```yaml
multi_material:
  mode: color
  reason: Readable direction markings.
  feeder: ams-2-pro
  primary: shell
  bed_temperature_c: 55
  materials:
    - id: shell
      type: PLA
      profile: Bambu PLA Basic @BBL P1S 0.4 nozzle
      color: '#264C43'
      nozzle_temperature_c: [190, 240]
      bed_temperature_c: [35, 65]
    - id: mark
      type: PLA
      profile: Bambu PLA Basic @BBL P1S 0.4 nozzle
      color: '#F2DDB4'
      nozzle_temperature_c: [190, 240]
      bed_temperature_c: [35, 65]
  regions:
    - id: shell-region
      body: lid
      path: stl/shell.stl
      material: shell
      expected_shells: 1
    - id: arrow-region
      body: lid
      path: stl/arrow.stl
      material: mark
      expected_shells: 1
```

Use two to four material entries, in project-filament order. Names and hex colors
are explicit; profile names must match the selected installed presets at export.
Use the actual filament manufacturer's ranges, not this example's values for a
different product. All materials share the selected bed temperature. Each nozzle
range stays within the P1S's 300 C limit; the bed stays within 100 C. Slicer
profiles must use nozzle temperatures within their material's declared range.

`manufacturing.material` equals the primary material's type. Bodies without
regions use the primary material, or an explicit `material: <id>` on their
`geometry.stl_files[]` entry. Bodies with regions assign material to every region
instead. A region cannot reuse a composite STL path. `min_wall_mm` on a region
defaults to two nozzle widths and cannot be lower; the composite retains the
whole part's existing wall/feature requirements.

In `support-interface` mode, set `interface_material` to a dedicated material id
and a non-`none` supports policy. Initial supported model materials are PLA/PETG;
dedicated interface types are `Support for PLA/PETG`, dry `PVA`, and dry `BVOH`.
PVA/BVOH entries require `dry: true` from actual preparation. Support materials
cannot be model regions. Support settings use model filament for the base and
the dedicated filament for the interface, zero contact gap/interface spacing,
and disable flushing into model infill. Confirm removal access in the design.

`functional` mode requires:

```yaml
  bond_test:
    source: measured  # or fit-tested
    report: fit/material-pair-test.md
```

The report must exist at delivery and describe actual testing. File existence
does not independently authenticate the physical result. No sample report is
supplied to impersonate a successful test.

The existing L3 handbook load gate does not model a mixed-polymer section and
rejects functional material plans for moment-section certification. Obtain an
independent material/joint analysis; the report does not change that model.

The executable adapter is initially scoped to one P1S plus one AMS 2 Pro. It
does not extrapolate newer printer features. It emits one plate per independent
printed body; all its regions share one translation and native `assemble_index`.
`material-plan.json` records source-relative meshes and their geometry digests.
`assemble-list.json` uses absolute paths for the local CLI and is regenerated
when a project moves; it is not included in the portable pack.
