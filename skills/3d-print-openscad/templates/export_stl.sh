#!/usr/bin/env bash
# Export STL via Docker OpenSCAD (no root install required on host).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_NAME="${1:-$(basename "$(ls "$ROOT"/src/*.scad | head -1)" .scad)}"
SRC="${ROOT}/src/${SRC_NAME}.scad"
OUT="${ROOT}/stl/${SRC_NAME}.stl"
IMG="${OPENSCAD_IMAGE:-openscad/openscad:2021.01}"

if [[ ! -f "$SRC" ]]; then
  echo "Missing source: $SRC" >&2
  exit 1
fi

mkdir -p "${ROOT}/stl" "${ROOT}/renders"

echo "Rendering ${SRC} -> ${OUT}"
docker run --rm \
  -v "${ROOT}:/work" \
  -w /work \
  "${IMG}" \
  openscad -o "/work/stl/${SRC_NAME}.stl" \
    --export-format=binstl \
    "/work/src/${SRC_NAME}.scad"

# Best-effort ownership fix when Docker writes as root
if [[ -f "$OUT" ]] && [[ ! -w "$OUT" || "$(stat -c %u "$OUT" 2>/dev/null)" == "0" ]]; then
  docker run --rm -v "${ROOT}:/work" alpine \
    chown "$(id -u):$(id -g)" "/work/stl/${SRC_NAME}.stl" 2>/dev/null || true
fi

ls -lh "${OUT}"
echo "Done."
