#!/usr/bin/env bash
# Detect whether FeynArts is installed and registered. Exit 0 if ready.
#
# Tiered check:
#   1. Config fast path: feynarts_path + feynarts_version match the pin.
#   2. Slow probe: only if HEPPH_FORCE_PROBE=1 or fast path missed.
#      Slow probe = $feynarts_path/FeynArts.m present (cheap; no
#      wolframscript invocation).
#   3. Deep functional probe (opt-in, HEPPH_FEYNARTS_DEEP_PROBE=1): actually
#      run InitializeModel[] via smoke_test_feynarts.sh. File presence is NOT
#      proof FeynArts works — Needs["FeynArts`"] succeeds even on a Wolfram
#      Engine that SIGSEGVs while parsing Models/Lorentz.gen (the WE 14.x+
#      regression; see INSTALL.md "## Wolfram Engine version compatibility").
#      Kept opt-in because it launches (and may crash) a wolframscript kernel,
#      which is too heavy/destructive for every preflight call.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_FEYNARTS_VERSION:-3.11}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("feynarts_path",""))
except Exception: pass' "$cfg")"
fi

# Fast path
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" feynarts "$recorded_path" "$PINNED_VERSION"; then
  if [ -z "${HEPPH_FORCE_PROBE:-}" ]; then
    exit 0
  fi
fi

# Slow path: file-presence + version-drift check.
[ -n "$recorded_path" ] || exit 1
[ -f "$recorded_path/FeynArts.m" ] || exit 1
# Version-drift: FeynArts ships under FeynArts-3.11/ — match the path.
set +e
bash "$SHARED/_detect_common.sh" path-version-match "$recorded_path" "$PINNED_VERSION"
rc=$?
set -e
[ $rc -eq 1 ] && exit 1

# Deep functional probe (opt-in): prove the generic model actually initializes,
# catching the Wolfram-Engine-version regression that file presence cannot. The
# smoke test exits 31 (FEYNARTS_ENGINE_INCOMPAT) when the kernel dies during
# InitializeModel[]; any nonzero exit here means "not functionally ready".
if [ -n "${HEPPH_FEYNARTS_DEEP_PROBE:-}" ]; then
  set +e
  bash "$SCRIPT_DIR/smoke_test_feynarts.sh" "$recorded_path" >/dev/null 2>&1
  smoke_rc=$?
  set -e
  [ "$smoke_rc" -ne 0 ] && exit 1
fi

exit 0
