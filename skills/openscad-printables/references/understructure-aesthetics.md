# Understructure aesthetics (elevated decks & equipment bases)

## Marc signals (2026-07-12)

1. v6 under preview: **“little cylinders … wouldn’t make sense.”** → pin stilts reject
2. v8 waffle: **“we don’t need that under the Spark”** → empty under seating deck for equipment
3. Compare to **real DGX / rack open-frames**: pocket + open air + rear I/O + perimeter structure

## Decision tree

```
Is this an elevated EQUIPMENT base (device with bottom vents, e.g. DGX Spark)?
  YES → Stackable / “stack on top”?
          YES → modular **U-sled** (preferred): open floor + short corner tabs outside chassis;
                males/cups; inter_gap ~10 mm; research community stacks if greenfield
                (see stackable-open-frame.md). Avoid tall four-post cage as default.
          NO  → OPEN FRAME: seating surface (hex/pocket); EMPTY under-volume;
                perimeter pillars + open side windows + open rear. NO waffle. NO pins.
  NO  → Does midspan of a solid tray need support for print/use?
          YES → soft waffle ribs (readable) or 8 soft buttresses + edge beam
          NO  → empty / minimal perimeter only
```

## Prefer by product class

| Class | Structure | Notes |
|-------|-----------|-------|
| **Equipment open frame** (default DGX) | Perimeter pillars + windowed skirt + thin edge beam under deck rim | Empty midspan under device; hex deck is seating only |
| **Stackable U-sled** (desk default) | Open floor + short corner tabs + U-rail + males/cups | Empty midspan; inter_gap ~10 mm; `stackable-open-frame.md` |
| Stackable open cube (archive) | Four full-height posts outside chassis | Rejected for desk sleeks (cage); DFM reference only |
| Soft elevated tray needing fill | Soft waffle under-ribs | Only when open frame hammocks |
| Soft buttresses (8) | Organic corner/mid ramps | Pair with edge beam |
| Edge beam / under-ring | Stiffens hex seating | Not a cavity fill |

## Avoid

- **Pin forest** — dense Ø2–3 mm cylinders (v4–v6). “Little cylinders.”
- **Waffle under equipment seating** — plastic with no product role when device vents bottom (v7–v8).
- Mid-air X-braces (v3).
- Solid vertical cell fill (v2) unless asked.

## Volume honesty (DGX stand)

| Ver | Under | cm³ | Verdict |
|-----|-------|-----|---------|
| v5.1 | unique stilts | 242.9 | pin look |
| v6 | load-path pins | 221.4 | aesthetic reject |
| v7 | waffle | 299.6 | readable but pointless under Spark |
| v8 | waffle top-first | 295.3 | same |
| **v9** | **open empty** | **163.1** | **active** (−45% vs waffle) |

Always report Δ cm³ when swapping understructure.

## Preview requirements

1. Solid under view — first-class when any understructure (or to prove empty open frame)
2. Cutaway if structure exists
3. Contact sheet includes under
4. Fail gate if underside looks like random pins

## Open frame pattern (equipment)

```
// seating: hex deck / pocket only
// empty clearance_z under deck interior
// corner pillars (soft hull) deck → feet
// optional thin outer skirt with large capsule windows
// edge_beam under deck perimeter only (not midspan fill)
// rear fully open for I/O
```

## Defaults

- Equipment bases: open frame, empty under, **no** waffle, **no** stilts
- Trays needing midspan: waffle `rib_t=2.8`, `rib_pitch=32`, `stilts_enable=false`
