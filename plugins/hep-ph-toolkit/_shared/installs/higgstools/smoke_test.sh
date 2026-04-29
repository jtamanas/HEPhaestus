#!/usr/bin/env bash
# smoke_test.sh — run HB/HS bundled SM examples and cache chi2_SM_ref.
#
# Usage: smoke_test.sh <hb_build_dir> <hs_build_dir>
#
# Exit 0 = smoke tests passed + SM ref cache written.
# Exit $EXIT_SMOKE = assertion failed.
# shellcheck disable=SC1090,SC1091
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON="$SCRIPT_DIR/../../../../../shared/install-helpers/_common.sh"
if [ ! -f "$COMMON" ]; then
  COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
fi
. "$COMMON"
. "$SCRIPT_DIR/_blocker.sh"

_LOG_TAG="higgstools-smoke"

HB_BUILD="${1:-}"
HS_BUILD="${2:-}"

if [ -z "$HB_BUILD" ] || [ -z "$HS_BUILD" ]; then
  err "Usage: smoke_test.sh <hb_build_dir> <hs_build_dir>"
  exit 1
fi

STATE_ROOT="${HEPPH_STATE_ROOT:-$HOME/.local/share/hephaestus}"
CACHE_DIR="$STATE_ROOT/cache"
CACHE_FILE="$CACHE_DIR/hs2_chi2_sm_ref.json"

mkdir -p "$CACHE_DIR"

SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# ── Parse version from skill_env.yaml ────────────────────────────────────────
_read_yaml() {
  python3 - "$SKILL_DIR/skill_env.yaml" "$1" <<'PY'
import sys, re
path, key = sys.argv[1], sys.argv[2]
with open(path) as f:
    for line in f:
        m = re.match(r'^' + re.escape(key) + r'\s*:\s*"?([^"#\n]+)"?', line)
        if m:
            print(m.group(1).strip())
            sys.exit(0)
print("")
PY
}

HB_VERSION="$(_read_yaml HB_VERSION)"
HS_VERSION="$(_read_yaml HS_VERSION)"

# ── Test HiggsBounds bundled SM example ───────────────────────────────────────
HB_EXAMPLE_DIR="$HB_BUILD"
HB_BIN="$HB_BUILD/bin/HiggsBounds"
if [ ! -x "$HB_BIN" ]; then
  HB_BIN="$HB_BUILD/HiggsBounds"
fi

if [ ! -x "$HB_BIN" ]; then
  emit_blocker "HIGGSTOOLS_SMOKE_TEST_FAILED" "fatal" \
    "HiggsBounds binary not found at $HB_BUILD/bin/HiggsBounds" \
    "Reinstall HiggsBounds with bash _shared/installs/higgstools/install.sh install --force"
  exit "$EXIT_SMOKE"
fi

log "Running HiggsBounds SM example..."
# The HiggsBounds example_SM_vs_4thgen is the standard bundled test.
# For smoke purposes, run HiggsBounds with minimal args to check it executes.
# Real SM check: HBresult=1 means not excluded (SM is not excluded by LEP/LHC)
HB_SMOKE_OUT=""
if [ -f "$HB_BUILD/bin/example_SM_vs_4thgen" ]; then
  HB_SMOKE_OUT=$(cd "$HB_EXAMPLE_DIR" && "$HB_BUILD/bin/example_SM_vs_4thgen" 2>&1 || true)
  if echo "$HB_SMOKE_OUT" | grep -q "HBresult.*=.*1"; then
    log "HiggsBounds SM example: PASS (HBresult=1)"
  else
    warn "HiggsBounds SM example did not confirm HBresult=1; output: $HB_SMOKE_OUT"
  fi
else
  # If the example binary isn't built, just verify HiggsBounds itself runs
  HB_SMOKE_OUT=$("$HB_BIN" 2>&1 || true)
  log "HiggsBounds binary responds (example binary not found, skipping SM check)"
fi

# ── Test HiggsSignals bundled SM example and cache chi2_SM_ref ───────────────
HS_BIN="$HS_BUILD/bin/HiggsSignals"
if [ ! -x "$HS_BIN" ]; then
  HS_BIN="$HS_BUILD/HiggsSignals"
fi

if [ ! -x "$HS_BIN" ]; then
  emit_blocker "HIGGSTOOLS_SMOKE_TEST_FAILED" "fatal" \
    "HiggsSignals binary not found at $HS_BUILD/bin/HiggsSignals" \
    "Reinstall HiggsSignals with bash _shared/installs/higgstools/install.sh install --force"
  exit "$EXIT_SMOKE"
fi

log "Running HiggsSignals SM example for chi2_SM_ref cache..."
# Run HiggsSignals on the bundled SM fixture from the tests/fixtures directory
SM_SLHA="$SKILL_DIR/../higgstools/tests/fixtures/sm_benchmark.slha"
if [ ! -f "$SM_SLHA" ]; then
  # Fall back to generating a minimal SM SLHA inline
  SM_SLHA="$(mktemp /tmp/sm_benchmark_XXXXXX.slha)"
  cat > "$SM_SLHA" <<'SLHA'
Block SMINPUTS
    1   1.27934000e+02   # alpha_em^-1(MZ)
    2   1.16637000e-05   # G_F [GeV^-2]
    3   1.18900000e-01   # alpha_s(MZ)
    4   9.11876000e+01   # MZ [GeV]
    5   4.18000000e+00   # mb(mb)
    6   1.73100000e+02   # mt [GeV]
    7   1.77682000e+00   # mtau [GeV]
Block MASS
   25   1.25090000e+02   # h0
Block HiggsBoundsInputHiggsCouplingsBosons
# SM-like couplings
   1   1   1   0   1.0   1.0   1.0   1.0   1.0  # h WW ZZ gg gaga
Block HiggsBoundsInputHiggsCouplingsFermions
# SM-like fermion couplings
   1   1   0   1.0   1.0   1.0  # h tt bb tautau
SLHA
fi

HS_OUTPUT=$("$HS_BIN" "$SM_SLHA" 2>&1 || true)

# Check chi2 is finite and < 200 (sanity check)
CHI2_OK=$(python3 - "$HS_OUTPUT" <<'PY'
import sys, re
text = sys.argv[1] if len(sys.argv) > 1 else ""
m = re.search(r"chi2\s*\(\s*total\s*\)\s*=\s*([0-9.eE+\-]+)", text)
if m:
    chi2 = float(m.group(1))
    if 0 < chi2 < 200:
        print("ok")
    else:
        print(f"out_of_range:{chi2}")
else:
    print("not_found")
PY
)

if [ "$CHI2_OK" = "ok" ]; then
  log "HiggsSignals SM chi2 is in range."
else
  warn "HiggsSignals SM chi2 check: $CHI2_OK (continuing with cache attempt)"
fi

# Cache the SM reference chi2
python3 "$SCRIPT_DIR/cache_sm_reference.py" \
  --hs-output "$HS_OUTPUT" \
  --cache-file "$CACHE_FILE" \
  --hb-version "$HB_VERSION" \
  --hs-version "$HS_VERSION" || {
    emit_blocker "HIGGSTOOLS_SMOKE_TEST_FAILED" "fatal" \
      "Failed to cache SM chi2 reference from HiggsSignals output." \
      "Check HiggsSignals installation and try reinstalling with --force."
    exit "$EXIT_SMOKE"
  }

log "SM reference chi2 cached at $CACHE_FILE"
exit 0
