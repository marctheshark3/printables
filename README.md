# Printables

Hermes manufacturing loop for **FDM parts**: text (+ optional photo) → locked intent → CAD backend → **fail-closed DFM gates** → zip STL for a Bambu Lab P1S-class bed.

This is the open-source skill pack we actually run. It is not a slicer, not a CAD GUI, and not a dump of household STLs.

```
intent (DESIGN.md)  →  OpenSCAD or Blender  →  dfm_gate.py  →  print notes + zip
```

## What you get

| Skill | Role | Maturity |
|-------|------|----------|
| `printables-part-brief` | Lock product class, orientation, fit provenance, never-list **before CAD** | Solid |
| `openscad-printables` | Parametric OpenSCAD + Docker `openscad/openscad:2021.01` export + scaffolds | Solid (default CAD) |
| `printables-dfm-gate` | Machine gates: topology, bed, overhang mass, open-under, fit/wet metadata | Solid (fail closed) |
| `blender-printables` | Headless `pblend` CLI for hex/Voronoi **lids**, not ported bases | Useful / sharp edges |
| `printables-display-enclosures` | Two-piece TFT/PyPortal desk shells (bezel face-on-bed) | Useful |
| `image-silhouette-print` | Icon → overlay QA → silhouette STL (stencils, ornaments) | Useful |
| `print-vs-buy-shop-fixtures` | Buy the pan/rack; print clips. Never print cages | Solid (policy) |
| `vibecad-printables` | Alternate CAD step via VibeCAD/FreeCAD | Alpha |

Honest scorecard: [STATUS.md](STATUS.md).

**Not in this repo:** household part libraries, private hub previews, printer queues, filament inventory, VibeCAD AppImages, or any credentials.

## Requirements

- Linux (this pack is used on aarch64 and x86_64)
- Python 3.11+ (stdlib; numpy optional)
- Docker, for OpenSCAD export: `openscad/openscad:2021.01`
- Optional: Blender ≥ 4.0 on `PATH` or `$BLENDER` for `pblend`
- Optional: [Hermes Agent](https://hermes-agent.nousresearch.com/docs) if you want the skills auto-loaded

## Install (Hermes)

```bash
git clone https://github.com/marctheshark3/printables.git
cd printables
./install.sh                  # every existing ~/.hermes/profiles/<name>
./install.sh --dry-run
HERMES_PROFILES=default ./install.sh
```

`install.sh` is **additive**. It does not `--delete` profile copies. We burned ourselves once shipping a stale pack over a newer `dfm_gate.py`.

After install, start a **new** Hermes session and use:

```
/printables bracket for this sensor  [optional image]
/printables-blender hex lid for a pi zero
```

You can also copy `skills/*` into any agent skill tree that understands `SKILL.md`.

## Use without Hermes

```bash
# New OpenSCAD project (writes DESIGN.md + scaffold)
THE_GRID="$HOME/print-projects" ./skills/openscad-printables/scripts/new_part.sh my-bracket bracket

# Export (needs Docker)
docker run --rm -v "$HOME/print-projects/my-bracket:/work" -w /work \
  openscad/openscad:2021.01 \
  openscad -o /work/stl/my-bracket.stl --export-format=binstl /work/src/my-bracket.scad

# Gate — HARD fail means do not ship
python3 skills/openscad-printables/scripts/dfm_gate.py \
  --project "$HOME/print-projects/my-bracket" \
  --stl "$HOME/print-projects/my-bracket/stl/my-bracket.stl" \
  --mode-file "$HOME/print-projects/my-bracket/docs/DESIGN.md"

# Blender path
./skills/blender-printables/scripts/pblend doctor
./skills/blender-printables/scripts/pblend new my-lid --class enclosure --root "$HOME/print-projects"
```

## Design laws that actually saved prints

1. **No CAD before `docs/DESIGN.md`.** Product class + print orientation + fit provenance first.
2. **Bottom-vent equipment is `equipment-open-frame`.** Empty under the seating deck. TOP-FIRST. No pin forest / waffle.
3. **Photos are not calipers.** Tag dims `measured` | `from-user` | `fit-tested` | `assumed`. Assumed precision fits cannot ship.
4. **OpenSCAD owns dimensional bases.** Blender owns organic/hex **lids**. Hybrid for full cases.
5. **A readable STL is not a printable one.** `dfm_gate.py` exit non-zero = not done.
6. **Buy stock, print intelligence.** Half-sheet pans and racks are cheaper than printed furniture.
7. **DFM PASS ≠ product.** Soft rounded meshes trip chord-length “thin” checks; stills still have to look like a tray, not a soap dish.

Defaults: P1S bed 256 mm, PETG preferred, min feature ≥ 1.6 mm, overhangs ≤ 45°, fit clearance ~0.5–1.0 mm/side.

## Layout

```
printables/
  install.sh
  STATUS.md
  skill-bundles/           # /printables and /printables-blender
  skills/
    printables-part-brief/
    openscad-printables/   # scaffolds + shared dfm_gate.py
    printables-dfm-gate/   # procedure only; script lives with OpenSCAD
    blender-printables/    # pblend + bpy_lib
    printables-display-enclosures/
    print-vs-buy-shop-fixtures/
    image-silhouette-print/
    vibecad-printables/
  examples/bracket-coupon/ # tiny DESIGN.md + SCAD, no household dims
  tests/                   # no Docker / no Blender required
```

## Tests

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s skills/blender-printables/scripts/tests -v
```

CI runs those. It does **not** export gold household fixtures. Those stay in a private working tree.

## License

MIT. See [LICENSE](LICENSE).
