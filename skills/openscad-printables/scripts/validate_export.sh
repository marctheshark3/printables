#!/usr/bin/env bash
# validate_export.sh — OpenSCAD Printables skill regression gates
# Canonical fixture: dgx-spark-stand v9
#
# Usage:
#   validate_export.sh [PROJECT_DIR] [VERSION] [--stl-only]
#   validate_export.sh                          # defaults → stand v9, re-export
#   validate_export.sh /path/to/proj v9 --stl-only
#
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${1:-$HOME/Documents/the-grid/dgx-spark-stand}"
VERSION="${2:-v9}"
STL_ONLY=0
for arg in "${@:3}"; do
  case "$arg" in
    --stl-only) STL_ONLY=1 ;;
  esac
done
# allow --stl-only as $2 when version omitted
if [[ "${2:-}" == "--stl-only" ]]; then
  VERSION="v9"
  STL_ONLY=1
fi

IMG="${OPENSCAD_IMAGE:-openscad/openscad:2021.01}"
PROJECT="$(cd "$PROJECT" && pwd)"

# Map version → filenames (stand convention)
case "$VERSION" in
  v10|10)
    SRC_BASE="dgx_spark_base_v10"
    GOLD_XY_MAX=210
    GOLD_Z_MAX=55
    GOLD_VOL_MIN=150
    GOLD_VOL_MAX=230
    EXPECT_OPEN_FRAME=1
    ;;
  v9|9)
    SRC_BASE="dgx_spark_base_v9"
    # prior gold (multi-volume pads; kept for history)
    GOLD_XY_MAX=200
    GOLD_Z_MAX=55
    GOLD_VOL_MIN=120
    GOLD_VOL_MAX=200
    EXPECT_OPEN_FRAME=1
    ;;
  v8|8)
    SRC_BASE="dgx_spark_base_v8"
    GOLD_XY_MAX=200
    GOLD_Z_MAX=55
    GOLD_VOL_MIN=200
    GOLD_VOL_MAX=350
    EXPECT_OPEN_FRAME=0
    ;;
  *)
    # generic: look for *${VERSION}* or basename match
    if [[ -f "$PROJECT/src/${VERSION}.scad" ]]; then
      SRC_BASE="$VERSION"
    elif [[ -f "$PROJECT/src/dgx_spark_base_${VERSION}.scad" ]]; then
      SRC_BASE="dgx_spark_base_${VERSION}"
    else
      # first scad in src/
      SRC_BASE="$(basename "$(ls "$PROJECT"/src/*.scad | head -1)" .scad)"
    fi
    GOLD_XY_MAX=256
    GOLD_Z_MAX=256
    GOLD_VOL_MIN=1
    GOLD_VOL_MAX=800
    EXPECT_OPEN_FRAME=0
    ;;
esac

SRC="$PROJECT/src/${SRC_BASE}.scad"
STL="$PROJECT/stl/${SRC_BASE}.stl"
PASS=0
FAIL=0
WARN=0

pass() { echo "  PASS  $*"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL  $*"; FAIL=$((FAIL + 1)); }
warn() { echo "  WARN  $*"; WARN=$((WARN + 1)); }

echo "=== openscad-printables validate ==="
echo "project: $PROJECT"
echo "version: $VERSION"
echo "source:  $SRC"
echo "stl:     $STL"
echo "skill:   $SKILL_DIR"
echo

# G1 source
if [[ -f "$SRC" ]]; then
  pass "G1 source exists"
else
  fail "G1 missing source: $SRC"
fi

# Re-export unless --stl-only
if [[ "$STL_ONLY" -eq 0 && -f "$SRC" ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    warn "Docker not found — skipping re-export; validating existing STL only"
  else
    echo "--- Docker export ($IMG) ---"
    mkdir -p "$PROJECT/stl"
    docker run --rm \
      -v "$PROJECT:/work" -w /work/src \
      "$IMG" \
      openscad -o "/work/stl/${SRC_BASE}.stl" \
        --export-format=binstl \
        "${SRC_BASE}.scad"
    # ownership fix
    if [[ -f "$STL" ]] && [[ "$(stat -c %u "$STL" 2>/dev/null || echo 0)" == "0" ]]; then
      docker run --rm -v "$PROJECT:/work" alpine \
        chown "$(id -u):$(id -g)" "/work/stl/${SRC_BASE}.stl" 2>/dev/null || true
    fi
  fi
fi

# G2 STL
if [[ -f "$STL" ]]; then
  pass "G2 STL exists ($(du -h "$STL" | awk '{print $1}'))"
else
  fail "G2 missing STL: $STL"
fi

# G7 product laws in SCAD (open-frame equipment)
if [[ -f "$SRC" && "$EXPECT_OPEN_FRAME" -eq 1 ]]; then
  if grep -qiE 'OPEN FRAME|empty under|NO waffle|TOP-FIRST|TOP FIRST' "$SRC"; then
    pass "G7 open-frame / TOP-FIRST language present in SCAD"
  else
    fail "G7 SCAD missing open-frame / empty-under / TOP-FIRST markers"
  fi
  if grep -qiE 'stilts_enable\s*=\s*true|pin forest|stilt_d\s*=' "$SRC" \
    && ! grep -qiE 'NO waffle|empty under|OPEN FRAME' "$SRC"; then
    fail "G7 SCAD looks pin/stilt oriented without open-frame markers"
  else
    pass "G7 no pin-forest-as-primary smell (or open-frame overrides)"
  fi
fi

# Mesh metrics via Python (numpy-stl or pure binary STL bbox/volume estimate)
if [[ -f "$STL" ]]; then
  METRICS="$(python3 - "$STL" <<'PY'
import struct, sys
from pathlib import Path
path = Path(sys.argv[1])
data = path.read_bytes()
# binary STL: 80 header + uint32 count + 50*n triangles
if len(data) < 84:
    print("ERR too_small")
    sys.exit(0)
n = struct.unpack_from("<I", data, 80)[0]
expected = 84 + n * 50
binary = expected <= len(data) + 50  # tolerate padding
mn = [1e30, 1e30, 1e30]
mx = [-1e30, -1e30, -1e30]
vol = 0.0
if binary and n > 0 and n < 50_000_000:
    off = 84
    for i in range(n):
        # normal 12 + 3 verts 36 + attr 2
        nx,ny,nz, x1,y1,z1, x2,y2,z2, x3,y3,z3 = struct.unpack_from("<12f", data, off)
        off += 50
        for x,y,z in ((x1,y1,z1),(x2,y2,z2),(x3,y3,z3)):
            if x < mn[0]: mn[0]=x
            if y < mn[1]: mn[1]=y
            if z < mn[2]: mn[2]=z
            if x > mx[0]: mx[0]=x
            if y > mx[1]: mx[1]=y
            if z > mx[2]: mx[2]=z
        # signed tetra volume vs origin
        vol += (
            x1*(y2*z3 - y3*z2)
            - y1*(x2*z3 - x3*z2)
            + z1*(x2*y3 - x3*y2)
        ) / 6.0
    dx, dy, dz = mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2]
    cm3 = abs(vol) / 1000.0
    print(f"OK tris={n} bbox={dx:.2f}x{dy:.2f}x{dz:.2f} vol_cm3={cm3:.2f}")
else:
    # ASCII or unknown — size only
    print(f"OK tris=? bbox=?x?x? vol_cm3=? size={len(data)}")
PY
)"
  echo "--- mesh ---"
  echo "  $METRICS"
  if [[ "$METRICS" == OK* ]]; then
    pass "G3 mesh readable (binary STL parse)"
    # parse bbox and volume
    BBOX="$(echo "$METRICS" | sed -n 's/.*bbox=\([0-9.]*\)x\([0-9.]*\)x\([0-9.]*\).*/\1 \2 \3/p')"
    VOL="$(echo "$METRICS" | sed -n 's/.*vol_cm3=\([0-9.]*\).*/\1/p')"
    if [[ -n "$BBOX" ]]; then
      read -r BX BY BZ <<< "$BBOX"
      # G5 bbox
      ok_xy=1
      awk -v x="$BX" -v y="$BY" -v m="$GOLD_XY_MAX" 'BEGIN{exit !((x<=m)&&(y<=m))}' || ok_xy=0
      ok_z=1
      awk -v z="$BZ" -v m="$GOLD_Z_MAX" 'BEGIN{exit !(z<=m)}' || ok_z=0
      if [[ "$ok_xy" -eq 1 && "$ok_z" -eq 1 ]]; then
        pass "G5 bbox ${BX}×${BY}×${BZ} mm within limits (XY≤${GOLD_XY_MAX}, Z≤${GOLD_Z_MAX})"
      else
        fail "G5 bbox ${BX}×${BY}×${BZ} mm outside limits (XY≤${GOLD_XY_MAX}, Z≤${GOLD_Z_MAX})"
      fi
      # P1S hard limit
      if awk -v x="$BX" -v y="$BY" 'BEGIN{exit !((x<256)&&(y<256))}'; then
        pass "G5b P1S bed fit (XY < 256)"
      else
        fail "G5b exceeds P1S bed (256 mm)"
      fi
    else
      warn "G5 could not parse bbox"
    fi
    if [[ -n "$VOL" && "$VOL" != "?" ]]; then
      if awk -v v="$VOL" -v a="$GOLD_VOL_MIN" -v b="$GOLD_VOL_MAX" 'BEGIN{exit !((v>=a)&&(v<=b))}'; then
        pass "G6 volume ${VOL} cm³ in band [${GOLD_VOL_MIN}, ${GOLD_VOL_MAX}]"
      else
        fail "G6 volume ${VOL} cm³ outside band [${GOLD_VOL_MIN}, ${GOLD_VOL_MAX}] (re-fill / wrong product?)"
      fi
      # waffle smell band for open-frame gold
      if [[ "$EXPECT_OPEN_FRAME" -eq 1 ]]; then
        if awk -v v="$VOL" 'BEGIN{exit !(v>=250)}'; then
          fail "G6b volume ${VOL} cm³ in waffle/pin band (≥250) — open frame should be leaner"
        else
          pass "G6b volume not in waffle reject band (≥250)"
        fi
      fi
    else
      warn "G6 volume not computed"
    fi
  else
    fail "G3 mesh parse failed: $METRICS"
  fi
fi

# G8 docs orientation
DOC_HIT=0
for f in "$PROJECT/docs/DESIGN_v9.md" "$PROJECT/docs/DESIGN.md" "$PROJECT/README.md"; do
  if [[ -f "$f" ]] && grep -qiE 'TOP-FIRST|top.first|feet[- ]?down|print[_ -]?orientation|rim on bed|bed face|flip' "$f"; then
    DOC_HIT=1
    break
  fi
done
if [[ "$DOC_HIT" -eq 1 ]]; then
  pass "G8 print orientation language found in DESIGN/README"
else
  warn "G8 no print orientation language in DESIGN/README"
fi

# S5 renders optional (version-tagged)
if ls "$PROJECT"/renders/${VERSION}_* >/dev/null 2>&1 || ls "$PROJECT"/renders/*${VERSION}* >/dev/null 2>&1; then
  pass "S5 ${VERSION} renders present"
elif find "$PROJECT/renders" -maxdepth 1 -type f -name '*.png' -size +0c -print -quit 2>/dev/null | grep -q .; then
  pass "S5 non-empty validation renders present"
else
  warn "S5 no non-empty validation renders"
fi

# G-dfm: manufacturing loop (overhang / thin / open-under / mode file)
DFM_PY="$SKILL_DIR/scripts/dfm_gate.py"
if [[ -f "$STL" && -f "$DFM_PY" ]]; then
  echo "--- dfm_gate.py ---"
  MODE_FILE=""
  for f in "$PROJECT/docs/DESIGN.md" "$PROJECT/docs/DESIGN_${VERSION}.md" "$PROJECT/docs/DESIGN_v10.md" "$PROJECT/docs/DESIGN_v9.md"; do
    if [[ -f "$f" ]]; then MODE_FILE="$f"; break; fi
  done
  DFM_ARGS=(python3 "$DFM_PY" --project "$PROJECT" --stl "$STL")
  if [[ -n "$MODE_FILE" ]]; then
    DFM_ARGS+=(--mode-file "$MODE_FILE")
  fi
  # Stand gold is open-frame; force class when EXPECT_OPEN_FRAME
  if [[ "$EXPECT_OPEN_FRAME" -eq 1 ]]; then
    DFM_ARGS+=(--product-class equipment-open-frame --print-orientation TOP-FIRST)
  fi
  if DFM_OUT="$("${DFM_ARGS[@]}" 2>&1)"; then
    echo "$DFM_OUT" | sed 's/^/  /'
    pass "G-dfm dfm_gate.py PASS"
  else
    echo "$DFM_OUT" | sed 's/^/  /'
    # If only missing DESIGN.md on legacy fixtures, degrade to warn when open-frame forced
    if echo "$DFM_OUT" | grep -q "G-mode: missing" && [[ "$EXPECT_OPEN_FRAME" -eq 1 ]]; then
      warn "G-dfm mode-file incomplete (legacy fixture) — mesh checks above still apply"
      # re-run without mode hard-fail by supplying forced flags only — already forced; count HARD lines excluding G-mode
      if echo "$DFM_OUT" | grep -E "HARD" | grep -vq "G-mode"; then
        fail "G-dfm HARD manufacturing fails (see above)"
      fi
    else
      fail "G-dfm dfm_gate.py FAIL (HARD manufacturing gates)"
    fi
  fi
else
  if [[ ! -f "$DFM_PY" ]]; then
    warn "G-dfm dfm_gate.py missing at $DFM_PY"
  fi
fi

echo
echo "=== summary: PASS=$PASS  FAIL=$FAIL  WARN=$WARN ==="
if [[ "$FAIL" -gt 0 ]]; then
  echo "RESULT: FAIL — skill regression / project gates not met"
  exit 1
fi
echo "RESULT: PASS"
exit 0
