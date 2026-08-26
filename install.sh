#!/usr/bin/env bash
# Install the validated 3D-print skill set into Hermes profiles.
set -euo pipefail

PACK="$(cd "$(dirname "$0")" && pwd)"
DRY=0
WITH_GROK=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --with-grok) WITH_GROK=1 ;;
    -h|--help)
      echo "Usage: $0 [--dry-run] [--with-grok]"
      echo 'Optional: HERMES_PROFILES="default tron"'
      exit 0
      ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

SKILLS=(
  3d-print-design-brief
  3d-print-openscad
  3d-print-blender
  3d-print-validate
  3d-print-display-enclosure
  3d-print-image-silhouette
  3d-print-shop-fixture
)
BUNDLES=(3d-print.yaml)

sync_dir() {
  local src="$1" dst="$2"
  if [[ "$DRY" -eq 1 ]]; then
    echo "DRY rsync $src -> $dst"
    return
  fi
  mkdir -p "$(dirname "$dst")"
  # Additive by design: installation must not erase local extensions.
  rsync -a --exclude='__pycache__' --exclude='*.pyc' "$src/" "$dst/"
  echo "installed $dst"
}

discover_profiles() {
  if [[ -n "${HERMES_PROFILES:-}" ]]; then
    echo "$HERMES_PROFILES"
    return
  fi
  if [[ ! -d "$HOME/.hermes/profiles" ]]; then
    echo ""
    return
  fi
  local names=()
  while IFS= read -r path; do names+=("$(basename "$path")"); done \
    < <(find "$HOME/.hermes/profiles" -mindepth 1 -maxdepth 1 -type d | sort)
  echo "${names[*]:-}"
}

PROFILES_STR="$(discover_profiles)"
if [[ -z "$PROFILES_STR" ]]; then
  echo "No Hermes profiles found; skills remain usable in this checkout."
else
  # shellcheck disable=SC2206
  PROFILES=($PROFILES_STR)
  for profile in "${PROFILES[@]}"; do
    profile_root="$HOME/.hermes/profiles/$profile"
    [[ -d "$profile_root" ]] || { echo "skip missing profile: $profile"; continue; }
    for skill in "${SKILLS[@]}"; do
      sync_dir "$PACK/skills/$skill" "$profile_root/skills/creative/$skill"
    done
    if [[ "$DRY" -eq 1 ]]; then
      echo "DRY cp $PACK/skill-bundles/3d-print.yaml -> $profile_root/skill-bundles/3d-print.yaml"
    else
      mkdir -p "$profile_root/skill-bundles"
      cp "$PACK/skill-bundles/3d-print.yaml" "$profile_root/skill-bundles/3d-print.yaml"
      chmod +x "$profile_root/skills/creative/3d-print-design-brief/scripts/"*.py 2>/dev/null || true
      chmod +x "$profile_root/skills/creative/3d-print-validate/scripts/"*.py 2>/dev/null || true
      chmod +x "$profile_root/skills/creative/3d-print-blender/scripts/pblend" 2>/dev/null || true
      chmod +x "$profile_root/skills/creative/3d-print-image-silhouette/scripts/"*.py 2>/dev/null || true
    fi
  done
fi

if [[ "$WITH_GROK" -eq 1 ]]; then
  for skill in "${SKILLS[@]}"; do
    sync_dir "$PACK/skills/$skill" "$HOME/.grok/skills/$skill"
  done
fi

cat <<EOF
Done. Start a new Hermes session, then use:
  /3d-print <part>
Validate directly:
  python3 "$PACK/skills/3d-print-validate/scripts/validate_project.py" <project>
EOF
