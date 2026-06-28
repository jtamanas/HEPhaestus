#!/usr/bin/env bash
# smoke_test_feynarts.sh — run a REAL FeynArts smoke test via wolframscript.
#
# Usage: smoke_test_feynarts.sh <feynarts_path>
#
# This test deliberately exercises the surface that actually breaks:
# InitializeModel[] — the generic-model load that parses Models/Lorentz.gen.
# A bare `Needs["FeynArts`"]` + `$FeynArtsVersion` check is NOT sufficient: the
# package loads fine even on a Wolfram Engine that SIGSEGVs the moment FeynArts
# tries to parse the generic Lorentz model (Wolfram Engine 14.x+ native
# regression — see INSTALL.md "## Wolfram Engine version compatibility").
# Checking only the load gives a FALSE GREEN.
#
# Two further subtleties this test handles:
#   1. Parse-time interning. In `wolframscript -code '...'`, a bare
#      `InitializeModel[...]` is interned into Global` at PARSE time, before
#      Needs[] runs, so it would resolve to an undefined Global` symbol and
#      return unevaluated WITHOUT ever calling FeynArts`InitializeModel — a
#      second false green. We defer resolution with ToExpression[] so the call
#      binds to FeynArts` after the package is loaded (same idiom as the
#      LoopTools B0 verification).
#   2. Kernel death. When the generic-model load crashes, the wolframscript
#      child dies with a signal (exit 139 = SIGSEGV) rather than returning a
#      WL error. We capture the abnormal/nonzero exit and report an actionable
#      diagnosis instead of a raw stack.
#
# Exits 0 if FeynArts loads AND InitializeModel[] completes (sentinel printed).
# Exits EXIT_FEYNARTS_SMOKE (28) on a generic smoke failure.
# Exits FEYNARTS_ENGINE_INCOMPAT (31) when the kernel dies during the generic
#   model load — i.e. the Wolfram-Engine-version regression. The blocker points
#   at INSTALL.md "## Wolfram Engine version compatibility".
# Emits {"status":"activation_required",...} to stdout when Wolfram needs activation.
#
# Reads wolfram_engine_path from config.

set -euo pipefail

_LOG_TAG="smoke_test_feynarts"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
. "$SHARED_COMMON"

WOLFRAM_HELPERS="$SCRIPT_DIR/../../../../shared/install-helpers/wolfram"
CHECK_ACTIVATION="$WOLFRAM_HELPERS/check_wolfram_activation.sh"
DETECT_WOLFRAM="$WOLFRAM_HELPERS/detect_wolfram.sh"

# Source blocker helper
. "$SCRIPT_DIR/_blocker.sh"

FEYNARTS_PATH="${1:-}"

if [ -z "$FEYNARTS_PATH" ]; then
  # Try to get from config
  FEYNARTS_PATH="$(config_get feynarts_path || true)"
fi

if [ -z "$FEYNARTS_PATH" ] || [ ! -f "$FEYNARTS_PATH/FeynArts.m" ]; then
  emit_blocker "FEYNARTS_PATH_INVALID" "fatal" \
    "FeynArts.m not found at '$FEYNARTS_PATH'." \
    "Provide a valid FeynArts directory via bash _shared/installs/feynarts/install.sh use-path <dir>."
  exit 27
fi

# Get wolframscript path.
. "$DETECT_WOLFRAM"
WS="$(detect_wolfram_path)"
if [ -z "$WS" ]; then
  emit_blocker "WOLFRAM_KERNEL_ABSENT" "fatal" \
    "wolframscript binary not found." \
    "Run /install to install Wolfram Engine first."
  exit "$EXIT_NO_WOLFRAM"
fi

# Optional FeynArts-only kernel override (the documented coexistence remedy).
# When feynarts_wolfram_kernel (config) or HEPPH_FEYNARTS_WOLFRAM_KERNEL (env)
# points at an older, validated WolframKernel binary, pass it to wolframscript
# as `-local <kernel>` so FeynArts runs on that engine while everything else
# stays on the global one. Until it is configured we fall back to the global
# wolframscript — the engine that exhibits the regression — so on a bare 14.x+
# machine this test is EXPECTED to fail, and that failure is the correct signal.
FA_KERNEL="${HEPPH_FEYNARTS_WOLFRAM_KERNEL:-$(config_get feynarts_wolfram_kernel || true)}"
WS_ARGS=()
if [ -n "$FA_KERNEL" ] && [ -e "$FA_KERNEL" ]; then
  WS_ARGS+=(-local "$FA_KERNEL")
  log "Using FeynArts-only Wolfram kernel: $FA_KERNEL"
fi

log "Running FeynArts smoke test (path=$FEYNARTS_PATH)..."

# Build the WL probe. Single-quote the WL fragments so bash leaves $Path,
# the FeynArts` backtick context, and $FeynArtsVersion untouched; inject the
# install path via double-quoted concatenation. ToExpression["InitializeModel[]"]
# defers symbol resolution until AFTER Needs[] (avoids parse-time interning into
# Global`). FEYNARTS_INIT_OK is printed ONLY if the generic model load returns.
WL_CODE='AppendTo[$Path, "'"$FEYNARTS_PATH"'"]; '
WL_CODE+='Needs["FeynArts`"]; '
WL_CODE+='Print["FEYNARTS_VERSION ", FeynArts`$FeynArtsVersion]; '
WL_CODE+='ToExpression["InitializeModel[]"]; '
WL_CODE+='Print["FEYNARTS_INIT_OK"]'

# Run the smoke test. The kernel may die with a signal (SIGSEGV → exit 139)
# while parsing Lorentz.gen; capture the exit code without tripping `set -e`.
# Note: ${WS_ARGS[@]+...} guard keeps an empty array safe under `set -u`
# (macOS bash 3.2 treats "${empty[@]}" as an unbound-variable error).
SMOKE_OUT="$("$WS" ${WS_ARGS[@]+"${WS_ARGS[@]}"} -code "$WL_CODE" 2>&1)" \
  && SMOKE_RC=0 || SMOKE_RC=$?

# --- 1. Happy path: package loaded AND generic model initialized. ---
if [ "$SMOKE_RC" -eq 0 ] && printf '%s' "$SMOKE_OUT" | grep -q 'FEYNARTS_INIT_OK'; then
  VERSION="$(printf '%s' "$SMOKE_OUT" | grep -Eo '[0-9]+\.[0-9]+' | head -n1 || true)"
  [ -n "$VERSION" ] || VERSION="unknown"
  log "FeynArts smoke test passed: InitializeModel[] completed (version=$VERSION)."
  printf '{"status":"ok","version":"%s"}\n' "$VERSION"
  exit 0
fi

# --- 2. Kernel death during the generic model load = the WE-version regression.
# A signal kill surfaces as exit code >= 128 (139 = 128 + SIGSEGV). The engine
# may also print a misleading "exited because of a license error" line on the
# same crash; treat the signal/abnormal-termination markers as authoritative. ---
CRASH=0
if [ "$SMOKE_RC" -ge 128 ]; then
  CRASH=1
elif printf '%s' "$SMOKE_OUT" | grep -qiE 'segmentation|exited because|kernel (died|quit|terminated)|abnormal termination|fatal error'; then
  CRASH=1
fi

if [ "$CRASH" -eq 1 ]; then
  log "FeynArts smoke test: kernel died during InitializeModel[] (exit $SMOKE_RC)."
  WS_VER="$("$WS" -code 'Print[$VersionNumber]' 2>/dev/null | grep -Eo '[0-9]+\.[0-9]+' | head -n1 || true)"
  emit_blocker "FEYNARTS_ENGINE_INCOMPAT" "fatal" \
    "FeynArts loaded but the Wolfram kernel CRASHED (exit $SMOKE_RC) while InitializeModel[] parsed Models/Lorentz.gen. This is the Wolfram Engine ${WS_VER:-14.x+} native regression, NOT a FeynArts bug — Needs[\"FeynArts\`\"] succeeds but the generic model load SIGSEGVs." \
    "Install an older, validated Wolfram Engine (recommended 13.3, fallback 12.3) for FeynArts ONLY and point feynarts_wolfram_kernel / HEPPH_FEYNARTS_WOLFRAM_KERNEL at its WolframKernel binary. See _shared/installs/feynarts/INSTALL.md section '## Wolfram Engine version compatibility — critical'." \
    "{\"wolframscript\":\"$WS\",\"engine_version\":\"${WS_VER:-unknown}\",\"exit_code\":$SMOKE_RC}"
  exit 31
fi

# --- 3. Activation required (engine present but not licensed). ---
ACTIVATION_JSON="$(printf '%s' "$SMOKE_OUT" | python3 "$WOLFRAM_HELPERS/_activation_parse.py" "$SMOKE_RC" 2>/dev/null || true)"
ACTIVATION_STATUS="$(printf '%s' "$ACTIVATION_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || true)"

if [ "$ACTIVATION_STATUS" = "activation_required" ]; then
  log "Wolfram Engine requires activation."
  printf '%s\n' "$ACTIVATION_JSON"
  exit 0
fi

# --- 4. Generic smoke failure (loaded but InitializeModel did not complete and
# the kernel did not crash — e.g. an unexpected WL error). ---
emit_blocker "FEYNARTS_SMOKE_TEST" "fatal" \
  "FeynArts smoke test failed: InitializeModel[] did not complete (exit $SMOKE_RC, no FEYNARTS_INIT_OK sentinel)." \
  "Check Wolfram Engine activation and FeynArts installation. If the kernel crashed, see INSTALL.md '## Wolfram Engine version compatibility — critical'."
exit 28
