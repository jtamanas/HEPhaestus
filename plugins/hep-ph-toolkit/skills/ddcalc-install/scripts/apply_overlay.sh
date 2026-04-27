#!/usr/bin/env bash
# Apply a DDCalc experiment overlay to a source tree.
# Usage: apply_overlay.sh <src_dir> <overlay_name>
# Exit: 0 on success; non-zero with blocker JSON on stderr on failure.
#
# NOTE: DDCALC_OVERLAY_NOT_SUPPORTED_V1
# In v1, overlays are DEFERRED. DDCalc 2.2.0 uses a central-dispatcher
# pattern requiring edits to DDExperiments.f90, include/DDExperiments.hpp,
# AND Makefile per new experiment. git apply --3way across three
# simultaneously-edited files is structurally fragile.
# Overlay plumbing is in place for v1.1 but all stub overlays emit this
# fatal blocker in v1.
#
# This gate is enforced by test_no_reference_fallback.py (grep for
# DDCALC_OVERLAY_NOT_SUPPORTED_V1 confirms it's present and not bypassed).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
. "$SHARED_COMMON"

_tag="ddcalc-overlay"

SRC_DIR="${1:?src_dir required}"
OVERLAY_NAME="${2:?overlay_name required}"

OVERLAYS_DIR="$SCRIPT_DIR/../overlays"
OVERLAY_DIR="$OVERLAYS_DIR/$OVERLAY_NAME"
MANIFEST="$OVERLAY_DIR/manifest.yaml"

if [ ! -d "$OVERLAY_DIR" ]; then
  "$SCRIPT_DIR/_blocker.sh" DDCALC_OVERLAY_MISSING \
    "Overlay directory not found: $OVERLAY_DIR" \
    "{\"overlay\":\"$OVERLAY_NAME\"}" >&2
  exit 1
fi

if [ ! -f "$MANIFEST" ]; then
  "$SCRIPT_DIR/_blocker.sh" DDCALC_OVERLAY_MISSING \
    "Overlay manifest.yaml not found: $MANIFEST" \
    "{\"overlay\":\"$OVERLAY_NAME\"}" >&2
  exit 1
fi

# DDCALC_OVERLAY_NOT_SUPPORTED_V1 gate
# Check if manifest has deferred: v1.1 — if so, emit the v1 blocker.
IS_DEFERRED="$(python3 - "$MANIFEST" <<'PY'
import yaml, sys
data = yaml.safe_load(open(sys.argv[1]))
print("1" if data.get("deferred") else "0")
PY
)"

if [ "$IS_DEFERRED" = "1" ]; then
  "$SCRIPT_DIR/_blocker.sh" DDCALC_OVERLAY_APPLY_FAILED \
    "DDCALC_OVERLAY_NOT_SUPPORTED_V1: overlay '$OVERLAY_NAME' is deferred to v1.1. DDCalc 2.2.0 uses a central-dispatcher registration pattern (DDExperiments.f90 + include/DDExperiments.hpp + Makefile). Overlay patches require multi-file edits that are structurally fragile with git apply --3way. See docs/roadmap/v1-constraints-work/ddcalc/plan/verifications.md §overlay-feasibility." \
    "{\"overlay\":\"$OVERLAY_NAME\",\"blocker_tag\":\"DDCALC_OVERLAY_NOT_SUPPORTED_V1\"}" >&2
  exit 1
fi

# ── v1.1+ path (reached only when overlay manifest has deferred: false/absent) ──
log "Applying overlay: $OVERLAY_NAME"

REJECT_FILES=()

while IFS= read -r patch_file; do
  [ -z "$patch_file" ] && continue
  full_patch="$OVERLAY_DIR/patches/$patch_file"
  [ ! -f "$full_patch" ] && { warn "Patch file not found: $full_patch"; continue; }

  log "Applying patch: $patch_file"
  if ! (cd "$SRC_DIR" && git apply --3way --whitespace=nowarn "$full_patch" 2>&1); then
    # Collect reject files
    mapfile -t new_rejects < <(find "$SRC_DIR" -name "*.rej" -newer "$MANIFEST" 2>/dev/null || true)
    REJECT_FILES+=("${new_rejects[@]}")
    warn "Patch $patch_file produced rejects."
  fi
done < <(python3 - "$MANIFEST" <<'PY'
import yaml, sys
data = yaml.safe_load(open(sys.argv[1]))
for exp in data.get("experiments", []):
    pf = exp.get("patch_file", "")
    if pf:
        print(pf.replace("patches/", ""))
PY
)

if [ ${#REJECT_FILES[@]} -gt 0 ]; then
  REJECTS_JSON="$(python3 -c "import json; print(json.dumps(${REJECT_FILES[*]@Q}))" 2>/dev/null || echo '[]')"
  "$SCRIPT_DIR/_blocker.sh" DDCALC_OVERLAY_APPLY_FAILED \
    "Overlay '$OVERLAY_NAME' produced patch reject files." \
    "{\"overlay\":\"$OVERLAY_NAME\",\"patch_reject_files\":$REJECTS_JSON}" >&2
  exit 1
fi

# Copy efficiency tables
while IFS= read -r eff_info; do
  [ -z "$eff_info" ] && continue
  eff_name="${eff_info%%:*}"
  eff_sha="${eff_info##*:}"
  src_eff="$OVERLAY_DIR/data/$eff_name"
  dst_eff="$SRC_DIR/data/experiments/$eff_name"

  if [ -f "$src_eff" ]; then
    mkdir -p "$(dirname "$dst_eff")"
    cp "$src_eff" "$dst_eff"
    verify_checksum "$dst_eff" "$eff_sha"
    log "Installed efficiency table: $eff_name"
  fi
done < <(python3 - "$MANIFEST" <<'PY'
import yaml, sys
data = yaml.safe_load(open(sys.argv[1]))
for exp in data.get("experiments", []):
    ef = exp.get("eff_file","").split("/")[-1] if exp.get("eff_file") else ""
    sha = exp.get("eff_sha256","")
    if ef and sha and sha != "STUB_SHA256_TO_BE_COMPUTED_AT_OVERLAY_PUBLICATION":
        print(f"{ef}:{sha}")
PY
)

log "Overlay '$OVERLAY_NAME' applied successfully."
