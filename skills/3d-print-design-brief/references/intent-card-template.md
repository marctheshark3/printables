# Intent card template → `docs/DESIGN.md`

Copy and fill. Narrative only; `docs/PRINT_SPEC.yaml` is the machine contract.

```markdown
---
product_class: equipment-open-frame
print_orientation: TOP-FIRST
print_up_axis: Z
use_flip: yes
soft_mode: yes
stack_story: none
clearance_mm: 0.8
expected_components: 1
fit_required: yes
critical_fit_status: measured
service_environment: dry
drainage: none
min_feature_mm: 1.6
overhang_max_deg: 45
material: PETG
printer: Bambu Lab P1S
scaffold: open_frame_equipment_scaffold.scad
image_role: none
---

# <part-name> — design intent

## Intent card
- **Product:** …
- **Product class:** equipment-open-frame | tray | bracket | enclosure | pip-hinge | generative | other
- **Stack story:** none | modular U-sled | … (one path only)
- **Print orientation:** TOP-FIRST | feet-down | other — describe bed face
- **Use flip:** yes/no — how user orients after print
- **Expected components:** closed edge-connected shells in the exported STL
- **Fit evidence:** which mating dimensions are measured, from-user, fit-tested, or assumed
- **Service environment:** dry/wet; for wet parts state drainage, retention, material, and cleaning access
- **Air / vents / I/O:** …
- **Aesthetic refs:** soft? open frame? hex? …
- **Never-list:** pin forest under deck; mid-air X; posts inside chassis; …

## Dimensions
| Feature | Value (mm) | Source |
|---------|------------|--------|
| … | … | from-user / measured / assumed |

## Clearances
- Fit: … mm/side
- Fasteners: …

## Reference image
(If none: `image_role: none`)

- **Paths:** …
- **image_role:** metrology | style | context
- **Findings:** …
- **Assumed (not measured):** …

## Explore vs converge
- Mode: Explore (≤5 then pick) | Converge (budget 1–3)
- Change budget: …

## Scaffold handoff
Start from template: `…`
Ready for CAD: yes
```
