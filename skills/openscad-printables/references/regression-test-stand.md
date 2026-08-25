# Skill regression test — DGX Spark stand

**Fixture project:** `~/Documents/the-grid/dgx-spark-stand/`  
**Gold version:** **v10 SOFT OPEN FRAME** (`src/dgx_spark_base_v10.scad` → `stl/dgx_spark_base_v10.stl`)  
**Why this is the test:** every major skill law (TOP-FIRST, open-frame empty under, soft hex seating, no pin forest, volume honesty, single-solid Volumes:2, iteration history) was proven here. If the skill “works” but would re-introduce v6 pins or v8 waffle under the Spark, the skill failed.

## When to run

1. After editing `openscad-printables` SKILL.md, templates, or DFM references  
2. After any “improve the stand” / redesign session that claims skill compliance  
3. Before teaching a new agent “how we design desk hardware”  

## Quick command

From the skill directory (or any cwd):

```bash
# validate existing gold STL (no re-export)
bash ~/.grok/skills/openscad-printables/scripts/validate_export.sh \
  "$HOME/Documents/the-grid/dgx-spark-stand" v10 --stl-only

# full re-export + validate (Docker required)
bash ~/.grok/skills/openscad-printables/scripts/validate_export.sh \
  "$HOME/Documents/the-grid/dgx-spark-stand" v10
```

Project-local:

```bash
~/Documents/the-grid/dgx-spark-stand/scripts/export_v10.sh
```

## Hard gates (must pass)

| # | Gate | Pass criterion (v9 gold) |
|---|------|---------------------------|
| G1 | Source exists | `src/dgx_spark_base_v9.scad` |
| G2 | STL exists | `stl/dgx_spark_base_v9.stl` |
| G3 | Manifold | OpenSCAD / mesh tool reports **Simple: yes** (or watertight equivalent) |
| G4 | Volumes | Prefer **Volumes: 2** (single solid + exterior); explain if higher |
| G5 | Bbox | XY **≤ 256 mm** (P1S); gold ~**179.6 × 179.6 × 45.8 mm** |
| G6 | Volume band | Gold **~163 cm³**; reject if redesign re-inflates toward waffle band (~295+) without intent |
| G7 | Product laws in SCAD | Comments/echo: OPEN FRAME, empty under, TOP-FIRST, NO waffle |
| G8 | Orientation docs | DESIGN/README: print rim on bed · use flip |
| G9 | Under preview | Solid under view shows **empty** midspan (not pin forest / dense waffle) |
| G10 | Soft seating | Hex (or soft) deck is seating only — not solid plate under chassis |

## Soft gates (should pass for “skill-grade” deliverable)

| # | Gate | Pass criterion |
|---|------|----------------|
| S1 | Intent / form lock | `docs/DESIGN_v9.md` (or DESIGN) has keep/kill + orientation |
| S2 | Regression table | History v1→v9 volumes not erased |
| S3 | Fit knobs | `fit_clearance`, `clearance_z`, `plan_r` (or equivalents) exposed |
| S4 | Ghost chassis | Optional but preferred: 150×150×50.5 scale in hero |
| S5 | Contact sheet | iso + top + under + cutaway present under `renders/v9_*` |
| S6 | Re-export one-liner | README has Docker command |

## Behavioral tests (agent / skill logic)

These are **not** mesh metrics — they catch the failure modes that made v6–v8:

| ID | Prompt / situation | Correct skill behavior | Fail if agent… |
|----|--------------------|------------------------|----------------|
| B1 | “Make the stand more printable / add under support” | Keep open frame; maybe thicken pillars/edge beam; **no** pin forest | Adds stilts under Spark |
| B2 | “Print top first” | TOP-FIRST coords; structure from deck→feet; rim lips not free nubs into bed | Only flips feet-down model without rebuild |
| B3 | “Less plastic” on liked open frame | Param knobs (pillar_w, edge_beam, window); report Δ cm³ | Swaps to solid cells or full waffle |
| B4 | “This ain’t it / from scratch” | New form lock + optional new project dir; still open-under law | Polish hated silhouette |
| B5 | “Stack on top” | Point to **stack** product (U-sled), not tall cage on the stand | Turns single stand into tower cage |
| B6 | Soft / no 90° | plan fillets, hex openings, capsule windows | Square lattice language |
| B7 | Validate export | Runs validate / reports Simple + volume + bbox | Ships STL with no gates |

## Anti-gold (must NOT reappear as “active”)

| Reject pattern | Why | Seen in |
|----------------|-----|---------|
| Pin stilts under deck | “Little cylinders” aesthetic reject | v5–v6 |
| Soft waffle under Spark | Plastic with no product role; blocks airflow story | v7–v8 |
| Mid-air X-frame | Support hell | v3 |
| Full vertical cells | Plastic bomb | v2 |
| Feet-down default without doc | Conflicts TOP-FIRST law | v1–v7 lineage |

## Volume regression band (honesty)

| Ver | Understructure | ~cm³ | Status |
|-----|----------------|------|--------|
| v5.1 | unique stilts | 242.9 | reject look |
| v6 | load-path pins | 221.4 | reject look |
| v7 | waffle | 299.6 | reject product role |
| v8 | waffle + TOP-FIRST | 295.3 | orient ok, fill wrong |
| **v9** | **open empty** | **163.1** | **gold** |

A “successful” redesign that lands at ~250–300 cm³ **without** an intentional stiffness brief has likely re-filled the under-volume. Fail the skill behavior even if Simple:yes.

## What “skill improved” means against this test

1. Templates default to open-frame TOP-FIRST for equipment, not pin stilts  
2. SKILL.md / refs forbid waffle under bottom-vent gear  
3. `validate_export.sh` can gate the stand project  
4. Agent following the skill would **not** re-ship v6/v7 as “improvements”  
5. Explore/converge + intent card stop product-class thrash  

## Sister fixture (optional second gate)

`~/Documents/the-grid/dgx-spark-stack/` **v2 U-sled**:

- Open floor, short tabs outside chassis, pitch ~82.5 mm, ~147 cm³  
- Fail if posts inside chassis XY or full-cylinder pad severs males  

Use when testing **stack** mode specifically; stand remains the primary skill test.
