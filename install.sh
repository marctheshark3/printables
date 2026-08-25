#!/usr/bin/env bash
# install.sh — copy printables skills into Hermes profiles
# Usage:
#   ./install.sh
#   HERMES_PROFILES="default tron" ./install.sh
#   ./install.sh --dry-run
#   ./install.sh --with-grok
set -euo pipefail

PACK="$(cd "$(dirname "$0")" && pwd)"
DRY=0
WITH_GROK=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --with-grok) WITH_GROK=1 ;;
    -h|--help)
      echo "Usage: $0 [--with-grok] [--dry-run]"
      echo "  HERMES_PROFILES=\"default tron\" $0"
      exit 0
      ;;
  esac
done

SKILLS=(
  printables-part-brief
  openscad-printables
  printables-dfm-gate
  blender-printables
  printables-display-enclosures
  print-vs-buy-shop-fixtures
  image-silhouette-print
  vibecad-printables
)
BUNDLES=(printables.yaml printables-blender.yaml)

# Additive rsync only. Never --delete — a stale pack once wiped a good dfm_gate.py.
sync_dir() {
  local src="$1" dst="$2"
  if [[ "$DRY" -eq 1 ]]; then
    echo "DRY rsync $src -> $dst"
    return
  fi
  mkdir -p "$(dirname "$dst")"
  rsync -a "$src/" "$dst/"
  echo "installed $dst"
}

discover_profiles() {
  if [[ -n "${HERMES_PROFILES:-}" ]]; then
    echo "$HERMES_PROFILES"
    return
  fi
  local found=()
  if [[ -d "$HOME/.hermes/profiles" ]]; then
    while IFS= read -r d; do
      found+=("$(basename "$d")")
    done < <(find "$HOME/.hermes/profiles" -mindepth 1 -maxdepth 1 -type d | sort)
  fi
  if [[ ${#found[@]} -eq 0 ]]; then
    echo ""
  else
    echo "${found[*]}"
  fi
}

echo "=== printables install ==="
echo "pack: $PACK"

PROFILES_STR="$(discover_profiles)"
if [[ -z "$PROFILES_STR" ]]; then
  echo "No Hermes profiles found under ~/.hermes/profiles and HERMES_PROFILES is unset."
  echo "Skills are still usable in-place:"
  echo "  python3 $PACK/skills/openscad-printables/scripts/dfm_gate.py --help"
  echo "  $PACK/skills/blender-printables/scripts/pblend doctor"
else
  # shellcheck disable=SC2206
  PROFILES=($PROFILES_STR)
  for profile in "${PROFILES[@]}"; do
    HOME_P="$HOME/.hermes/profiles/$profile"
    if [[ ! -d "$HOME_P" ]]; then
      echo "skip missing profile: $profile"
      continue
    fi
    echo "--- profile: $profile ---"
    for s in "${SKILLS[@]}"; do
      src="$PACK/skills/$s"
      dst="$HOME_P/skills/creative/$s"
      if [[ ! -d "$src" ]]; then
        echo "missing skill source: $src" >&2
        exit 1
      fi
      sync_dir "$src" "$dst"
    done
    mkdir -p "$HOME_P/skill-bundles"
    for b in "${BUNDLES[@]}"; do
      bsrc="$PACK/skill-bundles/$b"
      bdst="$HOME_P/skill-bundles/$b"
      if [[ ! -f "$bsrc" ]]; then
        echo "missing bundle: $bsrc" >&2
        exit 1
      fi
      if [[ "$DRY" -eq 1 ]]; then
        echo "DRY cp $bsrc -> $bdst"
      else
        cp "$bsrc" "$bdst"
        echo "installed $bdst"
      fi
    done
    if [[ "$DRY" -eq 0 ]]; then
      chmod +x "$HOME_P/skills/creative/openscad-printables/scripts/"*.sh 2>/dev/null || true
      chmod +x "$HOME_P/skills/creative/openscad-printables/scripts/dfm_gate.py" 2>/dev/null || true
      chmod +x "$HOME_P/skills/creative/blender-printables/scripts/pblend" 2>/dev/null || true
      chmod +x "$HOME_P/skills/creative/image-silhouette-print/scripts/"*.py 2>/dev/null || true
    fi
  done
fi

if [[ "$WITH_GROK" -eq 1 ]]; then
  echo "--- grok ---"
  for s in "${SKILLS[@]}"; do
    src="$PACK/skills/$s"
    dst="$HOME/.grok/skills/$s"
    if [[ -d "$(dirname "$dst")" || "$DRY" -eq 1 ]]; then
      sync_dir "$src" "$dst"
    else
      mkdir -p "$HOME/.grok/skills"
      sync_dir "$src" "$dst"
    fi
  done
fi

echo
echo "Done. New Hermes sessions pick up skills."
echo "Invoke: /printables <part> | /printables-blender <organic part>"
echo "CLI:    $PACK/skills/blender-printables/scripts/pblend doctor"
echo "Gate:   python3 $PACK/skills/openscad-printables/scripts/dfm_gate.py --help"
echo "Canonical pack (edit here, re-run install): $PACK"
