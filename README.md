# Printables

Agent skills for designing and validating FDM 3D prints. Turn a part brief into parametric CAD, one STL per printable body, and a checked delivery pack.

```text
Define the part → Build CAD → Validate → Inspect → Pack and slice
```

Every project starts with `docs/PRINT_SPEC.yaml`: dimensions, tolerances, materials, and print requirements. VibeCAD handles dimensional parts; Blender handles organic or lattice geometry. Validation blocks delivery when the contract or exported geometry fails.

## Quick start

Requires Python 3.11+ and PyYAML. CAD backends run on Linux and have separate setup steps.

```bash
git clone https://github.com/marctheshark3/printables.git
cd printables
python3 -m pip install PyYAML
./install.sh
```

Start a new Hermes session, then ask:

```text
/3d-print bracket for this sensor
```

You can also use the scripts directly. Try validating a committed example without installing a CAD backend:

```bash
python3 skills/3d-print-validate/scripts/validate_project.py \
  examples/bracket-coupon-vibecad
```

See [getting started](docs/getting-started.md) for profile selection, backend setup, and use without Hermes.

## Find your way

| I want to… | Start here |
|---|---|
| Choose a skill | [Skill catalog](skills/README.md) |
| Follow a workflow | [Documentation and guides](docs/README.md) |
| Explore working projects | [Examples](examples/README.md) |
| Check support and known limits | [Project status](docs/status.md) |
| Contribute or run checks | [Contributing](CONTRIBUTING.md) · [Tests](tests/README.md) |

`HARD=0` means validation found no blocking failures. Inspect the part and its slicer output before printing. Live printer control belongs to the sibling `bambu-mcp` project.

MIT licensed. See [LICENSE](LICENSE) and [security guidance](SECURITY.md).
