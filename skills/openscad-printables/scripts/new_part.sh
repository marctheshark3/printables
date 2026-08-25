#!/usr/bin/env bash
# new_part.sh — scaffold a the-grid printables project
# Usage: new_part.sh <part-name> [product_class]
set -euo pipefail

NAME="${1:-}"
CLASS="${2:-other}"
if [[ -z "$NAME" ]]; then
  echo "Usage: new_part.sh <part-name> [product_class]" >&2
  exit 1
fi
# slug
SLUG="$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')"
ROOT="${THE_GRID:-$HOME/Documents/the-grid}/$SLUG"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -e "$ROOT" ]]; then
  echo "Already exists: $ROOT" >&2
  exit 1
fi

mkdir -p "$ROOT"/{src,stl,docs,renders,scripts}

# Pick scaffold and service defaults
USE_FLIP="no"
SERVICE_ENV="dry"
DRAINAGE="none"
case "$CLASS" in
  equipment-open-frame|open-frame)
    SRC_TEMPLATE="open_frame_equipment_scaffold.scad"
    ORIENT="TOP-FIRST"
    USE_FLIP="yes"
    ;;
  tray|soft)
    SRC_TEMPLATE="soft_part_scaffold.scad"
    ORIENT="TOP-FIRST"
    USE_FLIP="yes"
    ;;
  wet-fixture|wet)
    SRC_TEMPLATE="part_scaffold.scad"
    ORIENT="feet-down"
    CLASS="wet-fixture"
    SERVICE_ENV="wet"
    DRAINAGE="open-continuous"
    ;;
  pip-hinge|pip)
    SRC_TEMPLATE="pip_hinge_cones.scad"
    ORIENT="feet-down"
    CLASS="pip-hinge"
    ;;
  generative)
    SRC_TEMPLATE="generative_loadpath.scad"
    ORIENT="feet-down"
    ;;
  *)
    SRC_TEMPLATE="part_scaffold.scad"
    ORIENT="feet-down"
    ;;
esac

if [[ -f "$SKILL_DIR/templates/$SRC_TEMPLATE" ]]; then
  cp "$SKILL_DIR/templates/$SRC_TEMPLATE" "$ROOT/src/${SLUG}.scad"
fi
if [[ -f "$SKILL_DIR/templates/soft_helpers.scad" ]]; then
  mkdir -p "$ROOT/src/lib"
  cp "$SKILL_DIR/templates/soft_helpers.scad" "$ROOT/src/lib/soft_helpers.scad"
fi
if [[ -f "$SKILL_DIR/templates/export_stl.sh" ]]; then
  cp "$SKILL_DIR/templates/export_stl.sh" "$ROOT/scripts/export_stl.sh"
  chmod +x "$ROOT/scripts/export_stl.sh"
fi

cat > "$ROOT/docs/DESIGN.md" <<EOF
---
product_class: $CLASS
print_orientation: $ORIENT
print_up_axis: Z
use_flip: $USE_FLIP
soft_mode: no
stack_story: none
clearance_mm: 0.8
expected_components: 1
fit_required: no
critical_fit_status: none
service_environment: $SERVICE_ENV
drainage: $DRAINAGE
min_feature_mm: 1.6
overhang_max_deg: 45
material: PETG
printer: Bambu Lab P1S
scaffold: $SRC_TEMPLATE
image_role: none
---

# $SLUG — design intent

## Intent card
- **Product:** $NAME
- **Product class:** $CLASS
- **Stack story:** none
- **Print orientation:** $ORIENT
- **Use flip:** document after CAD
- **Expected components:** 1 — change if the intended STL contains multiple closed shells
- **Fit evidence:** set fit_required and critical_fit_status before modeling mating interfaces
- **Service environment:** for wet parts change service_environment, drainage, material, retention, and cleaning access
- **Never-list:** pin forest under seating deck; mid-air X-braces; posts inside chassis XY

## Dimensions
| Feature | Value (mm) | Source |
|---------|------------|--------|
| (fill) |  | from-user / measured / assumed |

## Reference image
image_role: none

## Explore vs converge
- Mode: Converge
- Change budget: 1–3

## Scaffold handoff
Start from template: \`$SRC_TEMPLATE\`
Ready for CAD: yes — fill intent before heavy geometry.
EOF

cat > "$ROOT/README.md" <<EOF
# $SLUG

Printables project for Bambu Lab P1S.

- Intent: \`docs/DESIGN.md\`
- Source: \`src/${SLUG}.scad\`
- Export: \`scripts/export_stl.sh ${SLUG}\` or Docker openscad
- Gates: \`validate_export.sh\` / \`dfm_gate.py\` from printables skill pack
EOF

echo "Created $ROOT"
echo "  class=$CLASS scaffold=$SRC_TEMPLATE orient=$ORIENT"
echo "Next: edit docs/DESIGN.md intent, then CAD, then validate."
