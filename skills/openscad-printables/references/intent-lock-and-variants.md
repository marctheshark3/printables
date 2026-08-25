# Intent lock, stack stories, multi-variant exploration

Lessons from DGX Spark stand / stack / hex campaigns (2026-07): “close but off” usually means **product intent drifted**, not missing fillets.

## 0. Intent card (before any SCAD)

Write 6 lines in DESIGN.md — no CAD until Marc agrees or defaults are explicit:

```
Product one-liner: …
Stack story (how N units sit): …     # must be physically unambiguous
Seat orientation: flat | on-side
Air: under-device only | inter-chassis gap | both
Aesthetic refs: 1–3 links/names (what “good” looks like)
Never: …                             # e.g. tall cage, pin forest, waffle under Spark
Print: TOP-FIRST | studs-down | …
```

**Stack story test:** if you cannot draw desk → part → device → part → device in one line without “or…”, intent is not locked.

### Bad stack stories (reject)

- “Platform under each Spark” *and* “upper platform on lower Spark” without choosing
- Tall posts that clear chassis but read as a cage
- Nest cups that only work for empty platforms while marketing “stack Sparks”

### Good stack stories (examples)

1. **Under-tray only:** desk → tray → Spark. No multi-Spark stack.  
2. **Interposer:** desk → Spark1 → interposer tray → Spark2 (tray sits on chassis top, soft pads).  
3. **Bay frame:** frame holds one Spark; frames stack on each other via corner registration (chassis never bears upper frame).  
4. **On-side dual cradle:** both Sparks vertical in one shell (Schwick class).

## 1. Two modes (don’t mix)

| Mode | When | Output |
|------|------|--------|
| **Explore** | “try directions / 3–5 versions / this ain’t it” | Divergent variants; **no** “print target” crown; force pick |
| **Converge** | liked direction or “make it printable / top-first” | Diff-only on one silhouette; change budget 1–3 |

After Explore: stop and ask **pick letter / hybrid**. Do not auto-start Converge on all five.

## 2. Why output still feels “off”

Common misses even when gates pass (Simple/volume/previews):

1. **Ghost chassis missing** — silhouette read wrong without 150×150×50.5 ghost  
2. **No dual-stack still** when stacking is claimed  
3. **Generic hex** — looks like a parametric sample, not furniture (Schwick = continuous shell language)  
4. **Studs read as stilts** — need shoulder mass, pad tips, proportion to deck thickness  
5. **Rim too thin / too tall** — retention vs sleek tradeoff never shown as knob  
6. **Inspiration late** — research after CAD, not before form lock  

## 3. Enhanced deliverable checklist (beyond Simple:yes)

- [ ] Intent card agreed  
- [ ] Mode: explore | converge labeled  
- [ ] Volume cm³ + Δ vs prior  
- [ ] Hero **with ghost Spark**  
- [ ] If stack claim: **2-unit assembly** still (ghost Sparks)  
- [ ] Under view for airflow honesty  
- [ ] One sentence “what’s still wrong / pick next”  
- [ ] Zip STLs; no orphan “active” on unpicked explores  

## 4. Meta loop (factory for desk hardware)

```
Intent card → (optional) 3 refs + must/nice/never
    → Explore ≤5 variants OR Converge from liked SCAD
    → Marc pick / hybrid knobs
    → DFM-only pass (orientation, shoulders, fit)
    → PLA fit-check → PETG
```

**Do not** invent a new product class when he only asked for print orientation.

## 5. Hybrid request pattern

When Marc says “A hex + C dish + top-first”:

1. Clone A SCAD  
2. Change budget: dish wall from C + TOP-FIRST only  
3. One STL, one name (e.g. v3F), not re-export all five unless asked  
