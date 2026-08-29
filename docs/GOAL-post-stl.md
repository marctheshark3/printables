# Goal: finish the manufacturing side of Printables

**Status:** ready to implement. Sibling of `docs/GOAL-stl-to-step.md` (CAD-side hole). This is the **after-STL** hole.
**Handoff:** execute this file as the full brief. Do not rediscover the gap list.
**This repo:** Printables. Follow `CONTRIBUTING.md`. PRINT_SPEC.yaml stays the only machine contract.
**Printer control:** lives in the sibling repo **`bambu-mcp`**, not here. Do not vendor MQTT, FTPS, access codes, or a live printer client into this pack.

Paste for the next agent:

> Execute `docs/GOAL-post-stl.md`. Gated STL is not a finished print. Add thickness audit, deliverable pack, fit-coupon loop, insert/thread library, slicer/3MF process card, and split-for-bed. Do not put Bambu LAN control in printables — consume the sibling `bambu-mcp` repo. Secrets stay in env / user config and must fail the existing CI secret scan if committed. Unit CI stays free of slicers and printers. Start at thickness + pack tests, not a live print.

---

## Job

Printables already does:

```text
PRINT_SPEC.yaml → CAD → one STL per body → validate_project.py → (optional) validate_assembly.py
```

The `/3d-print` bundle then says “inspect in the slicer” and “no raw STL without a zip.” Those steps are still human. STATUS already admits STL cannot prove wall thickness. Class skills name a zip pack and `fit.coupon` files that are not generated.

This goal closes that loop **without** making Printables a printer daemon.

```text
validate_project.py
  → thickness audit (mesh)
  → pack zip + print notes
  → fit coupon (optional, when fit.required)
  → 3MF / process card from PRINT_SPEC
  → [optional, another process] bambu-mcp upload/print
```

A live print is never required for HARD=0. A sliced 3MF is never required for unit CI.

---

## bambu-mcp stays a sibling

An agent already created repo **`bambu-mcp`**. That is the correct home for:

- LAN MQTT / FTPS to a Bambu P1S (or family)
- access code, serial, LAN IP
- camera, AMS, start/pause/stop
- uploading a sliced 3MF

Printables **consumes** that server. It does not grow an MCP server of its own.

| Lives in printables | Lives in bambu-mcp |
|---|---|
| PRINT_SPEC, CAD, gated STL/STEP | Printer session, MQTT, FTPS |
| Thickness, pack zip, coupons, process card, 3MF **from spec** | Send that 3MF to a machine |
| Machine *profile* name (`bambu-lab-p1s`) and build volume | Machine *identity* (IP, serial, access code) |
| Deterministic, no network | Needs LAN |

Optional glue in this pack (prose + env detection only):

- Skill text: after `3d-print-pack` / `3d-print-slice` HARD=0, an agent **may** call bambu-mcp if configured.
- Never start a print because an STL validated.
- Missing bambu-mcp or missing env → skip, exit 0 on the printables side. Same extra-extra pattern as `export_if_vibecad.py`.

Do not add bambu-mcp as a Git submodule. Do not copy its source. Cite it by repo name in README/STATUS.

### Secrets — do not commit

Already forbidden by `CONTRIBUTING.md` and `SECURITY.md`. Extend the CI grep in `.github/workflows/ci.yml` if needed.

**Never in git:**

- `BAMBU_ACCESS_CODE`, `BAMBU_SERIAL`, LAN IPs, MQTT passwords
- `.env`, `secrets.enc`, printer token files
- Home paths, Tailscale hostnames, household inventory

**Allowed in git:**

- Env **names** and a `.env.example` with empty placeholders
- `manufacturing.printer: bambu-lab-p1s` (a profile, not a host)
- Build volume `[256, 256, 256]`

**Runtime (user machine, not the repo):**

```bash
# sibling bambu-mcp / MCP client config — not committed
export BAMBU_IP=...
export BAMBU_ACCESS_CODE=...
export BAMBU_SERIAL=...
export BAMBU_MODEL=P1S
```

Printables tools read env if present and otherwise no-op. They must not print secret values in logs. This pack still has **no required GitHub Actions secrets**.

If a secret lands in history: stop, rotate the printer access code, do not rely on a delete commit (`SECURITY.md`).

---

## Done means (this pack)

A manufacturing-side change is done when:

1. `validate_project.py` can HARD-fail a body whose **measured mesh thickness** is below `geometry.min_wall_mm` (not only CAD parameters).
2. `3d-print-pack` writes a zip of PRINT_SPEC + source + STLs + stills + optional STEP + print notes + SHA-256 manifest. No absolute paths.
3. When `fit.required: true`, a coupon generator can emit `fit/<name>-coupon.stl` mapped to named parameters, and a measure-back command can set `source: fit-tested` from a recorded caliper value.
4. An insert/thread OpenSCAD library exists with datasheet or measured holes and a coupon; assumed insert diameters cannot ship.
5. `3d-print-slice` can emit a process card JSON (always) and a 3MF when a slicer CLI is present; missing slicer is skip, not a fake file.
6. Build-volume overflow can be repaired by a split-with-pins path that declares **two** STLs, not by shrinking in silence.
7. Unit CI still needs only PyYAML + pytest. No Bambu Studio, Orca, MQTT, or printer.
8. No access codes, IPs, or serials in the tree.

---

## Skills and tools

Copy patterns from `3d-print-validate` (fail-closed mesh) and `3d-print-image-silhouette` (small CLIs). Descriptions ≤60 chars, period, `author: Marc Mailloux, Hermes Agent`. Do **not** add these to `skill-bundles/3d-print.yaml` until they are green and optional extras are skippable. Prefer extending validate first so `/3d-print` gets thickness without a new bundle member.

### 1. Thickness audit — extend `3d-print-validate`

Not a new skill. STATUS today: “STL geometry cannot prove wall thickness.”

- Raycast or voxel thickness on each declared STL in print orientation.
- HARD if any sample below `geometry.min_wall_mm` over more than a tiny area fraction (name the fraction; default conservative).
- WARN near `min_feature_mm`.
- Short chords stay warning-only (existing).
- Tests: a 0.4 mm wall plate HARD-fails; the bracket coupon still passes.

Keep it stdlib if possible; numpy only as optional extra detected at runtime, never imported at module top-level of `validate_stl.py`.

### 2. Skill `3d-print-pack`

Description: `Zip a gated project into a deliverable pack.`

CLI `ppack` (or `pack_project.py`):

```bash
python3 skills/3d-print-pack/scripts/pack_project.py "$PROJECT"
```

Must include: `docs/PRINT_SPEC.yaml`, `cad.source_files`, every `geometry.stl_files[]`, optional `step/`, `renders/` stills if present, generated `docs/PRINT_NOTES.md` (orientation, bed face, supports, material, nozzle, layer height — **from the spec only**), `MANIFEST.sha256`.

Refuse to pack if `validate_project.py` would HARD-fail (call it, do not reimplement). pblend’s zip stays; this is the backend-neutral pack every class skill already asks for.

### 3. Fit coupon loop — extend design-brief + OpenSCAD templates

When `fit.required: true`:

- Template `fit/coupon.scad` (or generator) with the same named hole/clearance parameters as the part.
- One small STL, `expected_shells: 1`, same validate gates.
- `record_fit.py --parameter hole_d --measured-mm 4.15` updates PRINT_SPEC `source: fit-tested` and the nominal if the user said so. Never invent a measurement.

Assumed critical fits still cannot ship (existing rule).

### 4. Insert / thread library — `3d-print-openscad/references/` + templates

Not a new kernel. Add:

- `references/heat-set-inserts-fdm.md` — M2/M3/M4 brass insert OD, depth, boss OD, datasheet provenance.
- `templates/insert_boss.scad` and a coupon.
- Printed thread (ISO metric coarse) only as an explicit opt-in; default is heat-set.

Dimensions in PRINT_SPEC with `source: datasheet` or `measured`. `assumed` insert OD is HARD on fit-required parts.

### 5. Skill `3d-print-slice`

Description: `Emit a slicer process card and optional 3MF.`

CLI reads PRINT_SPEC `print:` + `manufacturing:` and writes `slice/<body>.process.json`:

- printer profile name, build volume, nozzle, layer height, material
- bed face, up axis, supports policy, max overhang
- per-body STL path

If `ORCA_SLICER` / `BAMBU_STUDIO` / `PRUSA_SLICER` is set and executable, also write `slice/<body>.3mf`. If not, skip 3MF and print `SKIP: no slicer CLI`. Never write an empty or STL-renamed “3MF”.

This skill does **not** talk to a printer. bambu-mcp consumes the 3MF later.

### 6. Split-for-bed — OpenSCAD template + small CLI

When envelope HARD fires:

- Split along a named plane.
- Alignment pins/keys with clearance_per_side from spec.
- Two `geometry.stl_files[]` entries, two bodies.
- Do not silently scale the part down.

Generator tests on a 300 mm bar vs 256 mm envelope.

### 7. Optional printer handoff (prose only in v1)

`3d-print-slice` SKILL.md “Afterward” section:

```text
If bambu-mcp is configured in the agent MCP list and BAMBU_* env is set,
the agent may upload slice/<body>.3mf. A validated STL is not permission
to print. user confirmation stays in bambu-mcp (write tools).
```

No Python MQTT in this repo in v1.

---

## PRINT_SPEC impact

Prefer **optional** fields so existing examples stay valid:

```yaml
pack:
  required: false          # true in class skills that already demand a zip

slice:
  process_card: slice/bracket.process.json   # optional path
  three_mf: slice/bracket.3mf                # optional; must exist if named

fit:
  required: true
  coupon: fit/bracket-coupon.stl
  measured_mm:            # optional measure-back
    hole_d: 4.18
```

Thickness uses existing `geometry.min_wall_mm`. Split uses existing `geometry.stl_files[]` (two entries). No printer IP field. Ever.

Update `print_spec.py`, `print-spec-v1.md`, and tests in the same PR as the fields.

---

## Tests and CI

Unit job (PyYAML + pytest only):

- Thin-wall fixture HARD-fails thickness
- Bracket coupon still HARD=0
- Pack zip contains spec + stl + manifest; fails if validate would fail
- Coupon generator names match PRINT_SPEC parameters
- Process card JSON matches spec print/manufacturing keys
- Split of oversized bar yields two bodies inside 256³
- Secret scan still fails on `BAMBU_ACCESS_CODE=`, LAN IPv4 next to `access_code`, and existing needles
- Prompt routing: “zip this gated project” → `3d-print-pack`; “slice this PRINT_SPEC” → `3d-print-slice`; printer “start this print on the P1S” must **not** outrank pack/slice as primary in **this** repo (that prompt belongs to bambu-mcp)

CAD job: no new apt. If a slicer appears on a developer machine, extra extra skip pattern.

Do not add bambu-mcp, Bambu Studio, or network tests to `.github/workflows/ci.yml`.

---

## Order of work

Each step leaves tests green. Do not start at a live print.

1. Thickness audit in `validate_stl.py` / `dfm.py` + fixtures.
2. `3d-print-pack` + PRINT_NOTES from spec + zip tests. Wire class skills to it (silhouette, display-enclosure).
3. Fit coupon template + `record_fit.py` measure-back.
4. Heat-set insert reference + OpenSCAD boss/coupon.
5. `3d-print-slice` process card; 3MF behind slicer detection.
6. Split-for-bed template + CLI.
7. README, STATUS, CONTRIBUTING, install.sh, `test_skill_contract.py`, secret-scan needles, optional bambu-mcp handoff paragraph.
8. Stop. Printer upload is bambu-mcp’s goal, not this one.

---

## Do not

- Vendor or submodule `bambu-mcp`
- Commit access codes, serials, LAN IPs, `.env`
- Start a print from `validate_project.py` HARD=0
- Require a slicer in unit CI
- Put MQTT/FTPS in this pack
- Parse DESIGN.md
- Add these skills to `/3d-print` until extras skip cleanly
- SLA, CNC, FEA, ROS, AMS-as-CAD
- Household inventory or machine-local paths (`CONTRIBUTING.md`)

---

## STATUS.md limits to record

- Thickness audit is sampled, not an exact-kernel wall proof.
- Pack zip is not a slicer project unless `3d-print-slice` ran.
- 3MF emission needs a local slicer CLI; CI does not ship one.
- Live Bambu control is the sibling `bambu-mcp` repo. This pack never stores printer secrets.
- Split-for-bed is an explicit repair of envelope HARD, not automatic.

---

## Working rules

Read this file, `docs/GOAL-stl-to-step.md` (do not reopen CAD reverse here), `CONTRIBUTING.md`, `SECURITY.md`, `skills/3d-print-validate/`, `skills/3d-print-design-brief/`. Stdlib first. Short factual comments. No `__pycache__`.

```bash
python3 -m pytest -q \
  skills/3d-print-design-brief/tests \
  skills/3d-print-validate/tests \
  skills/3d-print-pack/scripts/tests \
  skills/3d-print-slice/scripts/tests \
  tests/test_prompt_scenarios.py
python3 tests/test_skill_contract.py
```

## Checklist

- [x] Thickness HARD on a thin-wall fixture; coupon examples still pass
- [x] `3d-print-pack` zip + manifest; refuses ungated projects
- [x] Fit coupon generate + measure-back
- [x] Insert/thread reference + CAD template + coupon
- [x] Process card always; 3MF only if slicer present
- [x] Split-for-bed produces two valid bodies
- [x] bambu-mcp cited as sibling; no printer client in this tree
- [x] Secret scan catches access-code-like commits
- [x] Unit CI still PyYAML + pytest only
