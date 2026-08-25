# Reference: DGX Spark elevated passive base

**Path:** `~/Documents/the-grid/dgx-spark-stand/`  
**Printer:** Bambu Lab P1S  
**Current print target:** **v10 SOFT OPEN FRAME** — hex seating + **empty under Spark** + soft load-path legs; **TOP-FIRST**; **Volumes:2**.  
**Source:** `src/dgx_spark_base_v10.scad` → `stl/dgx_spark_base_v10.stl`

## Locked product

- Elevated passive desk base for NVIDIA DGX Spark  
- Chassis: **150 × 150 × 50.5 mm**, **1.2 kg**  
- Under-clearance **~35 mm empty** (airflow; Spark vents bottom)  
- Rear open: USB-C PD, HDMI, 10GbE, dual QSFP  
- Soft hex deck = seating only; not filled under-volume  

## Compare to real mounts

Commercial Spark rack/open frames: precision pocket/channel, open under/sides, rear clear, perimeter structure — **not** lattice fill under the unit.

## Version history (lessons)

| Ver | Idea | Volume (cm³) | Verdict |
|-----|------|--------------|---------|
| v1 | Lattice tray | ~172 | Liked form; bridge risk |
| v2 | Full cells | ~283–362 | Too much plastic |
| v3 | Mid-air X-frame | ~54 | Support hell |
| v4 | Stilts, square | ~174 | FDM-ok; not soft |
| v5.0 | Soft + 4 buttresses | ~194 | Hammock |
| v5.1 | Unique stilts + 8 buttresses | **242.9** | Pin-forest look |
| v6 | Load-path pins | **221.4** | **“Little cylinders” reject** |
| v7 | Soft waffle | **299.6** | Readable but **pointless under Spark** |
| v8 | Waffle + TOP-FIRST | **295.3** | Orientation correct; fill still wrong |
| v9 | Open frame empty under + TOP-FIRST | **163.1** | Product law; Volumes:7 (floating pads) |
| **v10** | Soft open frame + fused single solid | **187.3** | **Active · Volumes:2** |

## Design law (v9–v10)

1. Soft hex **seating deck** + rim pocket — keep  
2. **Empty under Spark** — no waffle, no pins  
3. Perimeter soft legs/pillars + open windowed apron + thin edge beam  
4. Rear fully open for I/O  
5. **TOP-FIRST:** rim on bed → feet free; flip for use  
6. **Fuse** locators/legs into body (volume overlap) → **Volumes:2**  
7. PETG; supports off expected  

## Export

```bash
~/Documents/the-grid/dgx-spark-stand/scripts/export_v10.sh
```

v10: `Simple: yes`, **Volumes: 2**, bbox **187.9 × 187.9 × 46.2 mm**, **187.3 cm³**.

## Delivery lessons

- Zip STL for Discord (raw MEDIA often fails)  
- Solid under view to prove empty open frame  
- Volume delta when structure changes  
- Form lock + change budget (iteration protocol)  

Hub: `(private local hub — not published)`

## Skill regression role

This project is the **canonical acceptance test** for `openscad-printables`.

- Spec: `references/regression-test-stand.md`
- Script: `scripts/validate_export.sh <project> v9 [--stl-only]`
- Gold: open frame empty under · TOP-FIRST · ~163 cm³ · no pin forest · no waffle under Spark

Any skill/template change that would reintroduce v6 pins or v7–v8 waffle as defaults is a skill regression.
