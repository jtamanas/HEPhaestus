#!/usr/bin/env bash
# install_formcalc_full.sh — full FormCalc 9.10 + LoopTools + FORM 4.3.1 install.
# Called by install_formcalc.sh for the `install` subcommand.
#
# Steps:
#  1. Wolfram Engine probe
#  2. gfortran check
#  3. Disk space check (3 GB min)
#  4. HEPPH_NO_NETWORK branch / network download
#  5. verify_checksum
#  6. Extract FormCalc
#  7. Register in $UserBaseDirectory/Applications/ via init.m
#  8. Build LoopTools
#  9. Download + build FORM 4.3.1
# 10. Run smoke_test.wls
# 11. config_merge nine keys
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGINS_DIR="$(cd "$SCRIPT_DIR/../../../../.." && pwd)/plugins"
SHARED_COMMON="$PLUGINS_DIR/shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then
  echo "[formcalc-install] ERROR: _common.sh not found at $SHARED_COMMON" >&2
  exit 1
fi
. "$SHARED_COMMON"
. "$PLUGINS_DIR/shared/install-helpers/atomic_write.sh"

_LOG_TAG="formcalc-install"

# ── Version pins ──────────────────────────────────────────────────────────────
# FormCalc 10.0 does not exist; latest is 9.10 (feynarts.de, 2024-10-11).
FORMCALC_VERSION="${HEPPH_FORMCALC_VERSION:-9.10}"
FORM_VERSION="${HEPPH_FORM_VERSION:-4.3.1}"
LOOPTOOLS_VERSION="${FORMCALC_VERSION}"

FORMCALC_SHA256="${HEPPH_FORMCALC_SHA256:-352bff193be4472ce38bb266fcccb653c3dee21c49c6df6c5b784ff8ad53029b}"

# ── Install root ──────────────────────────────────────────────────────────────
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
INSTALL_ROOT="${DATA_HOME}/hephaestus/formcalc-${FORMCALC_VERSION}"

# ── Download URL ──────────────────────────────────────────────────────────────
# FormCalc: feynarts.de canonical URL (verified live, HTTP 200).
FORMCALC_URL="https://feynarts.de/formcalc/FormCalc-${FORMCALC_VERSION}.tar.gz"

# ── Blocker helper ─────────────────────────────────────────────────────────────
blocker_json() {
  local code="$1" mode="$2" msg="$3" extra="${4:-}"
  if [ -n "$extra" ]; then
    printf '{"code":"%s","mode":"%s","message":"%s",%s}\n' "$code" "$mode" "$msg" "$extra" >&2
  else
    printf '{"code":"%s","mode":"%s","message":"%s"}\n' "$code" "$mode" "$msg" >&2
  fi
}

# ── Step 1: Wolfram Engine ────────────────────────────────────────────────────
log "Checking Wolfram Engine..."
WOLFRAM_BIN="$(config_get "wolfram_engine_path" 2>/dev/null || true)"
if [ -z "$WOLFRAM_BIN" ] || [ ! -x "$WOLFRAM_BIN" ]; then
  # Try scanning PATH
  WOLFRAM_BIN="$(command -v wolframscript 2>/dev/null || true)"
fi
if [ -z "$WOLFRAM_BIN" ] || [ ! -x "$WOLFRAM_BIN" ]; then
  blocker_json "WOLFRAM_KERNEL_ABSENT" "fatal" "wolframscript not found" \
    '"user_instruction":"Install Wolfram Engine free edition from https://www.wolfram.com/engine/ then rerun."'
  exit $EXIT_NO_WOLFRAM
fi
log "Wolfram Engine: $WOLFRAM_BIN"

# ── Step 2: gfortran ─────────────────────────────────────────────────────────
log "Checking gfortran..."
if ! command -v gfortran >/dev/null 2>&1; then
  blocker_json "FORMCALC_NO_GFORTRAN" "fatal" "gfortran not found in PATH" \
    '"user_instruction":"On macOS: brew install gcc. On Linux: sudo apt install gfortran or sudo dnf install gcc-gfortran"'
  exit $EXIT_NO_GFORTRAN
fi
log "gfortran: $(command -v gfortran)"

# ── Step 3: Disk space ────────────────────────────────────────────────────────
check_disk 3 5

# ── Step 4: Download FormCalc ─────────────────────────────────────────────────
mkdir -p "$INSTALL_ROOT"
FORMCALC_TARBALL="$INSTALL_ROOT/FormCalc-${FORMCALC_VERSION}.tar.gz"
log "Downloading FormCalc ${FORMCALC_VERSION}..."
download_with_retry "$FORMCALC_URL" "$FORMCALC_TARBALL" "FORMCALC"

# ── Step 5: Checksum ──────────────────────────────────────────────────────────
verify_checksum "$FORMCALC_TARBALL" "$FORMCALC_SHA256"

# ── Step 6: Extract ───────────────────────────────────────────────────────────
log "Extracting FormCalc ${FORMCALC_VERSION}..."
tar -xzf "$FORMCALC_TARBALL" -C "$INSTALL_ROOT" || {
  err "Extraction failed."
  exit $EXIT_EXTRACT
}

# Find extracted dir.
FORMCALC_SRC_DIR=""
for d in "$INSTALL_ROOT"/FormCalc-*; do
  if [ -d "$d" ] && [ -f "$d/FormCalc.m" ]; then
    FORMCALC_SRC_DIR="$d"
    break
  fi
done
if [ -z "$FORMCALC_SRC_DIR" ]; then
  err "FormCalc.m not found after extraction."
  exit $EXIT_EXTRACT
fi

# ── Step 7: Register in $UserBaseDirectory/Applications/ ──────────────────────
# Query UserBaseDirectory from wolframscript.
USER_BASE_DIR="$(
  "$WOLFRAM_BIN" -code 'Print[$UserBaseDirectory]' 2>/dev/null \
  | tr -d '\r\n' || true
)"
if [ -z "$USER_BASE_DIR" ]; then
  warn "Could not determine \$UserBaseDirectory; using fallback."
  USER_BASE_DIR="${HOME}/Library/Wolfram"  # macOS fallback
fi

APP_DIR="${USER_BASE_DIR}/Applications/FormCalc-${FORMCALC_VERSION}"
log "Registering FormCalc at $APP_DIR ..."
mkdir -p "$(dirname "$APP_DIR")"
if [ -d "$APP_DIR" ]; then
  rm -rf "$APP_DIR"
fi
cp -r "$FORMCALC_SRC_DIR" "$APP_DIR"
FORMCALC_PATH="$APP_DIR"

# Append to init.m so Needs["FormCalc`"] works.
INIT_DIR="${USER_BASE_DIR}/Kernel"
mkdir -p "$INIT_DIR"
INIT_FILE="${INIT_DIR}/init.m"
touch "$INIT_FILE"
if ! grep -q "FormCalc-${FORMCALC_VERSION}" "$INIT_FILE" 2>/dev/null; then
  printf '\nAppendTo[$Path, "%s"];\n' "$APP_DIR" >> "$INIT_FILE"
  log "Appended FormCalc path to $INIT_FILE"
fi

# ── Step 7b: Compile the $SystemID binaries FormCalc.m expects ────────────────
# FormCalc.m resolves its executables from  $FormCalcDir/$SystemID/ReadForm
# (FormCalc.m: $FormCalcBin = ToFileName[{$FormCalcDir, $SystemID}]), and also
# needs ToForm/ToFortran/ToC/reorder there. The 9.10 tarball ships only the FORM
# binaries + prebuilt ReadForm/ReadData under bin/$SystemID/; the per-arch
# $FormCalcDir/$SystemID directory is created by FormCalc's own ./compile
# script, which mcc-compiles ReadForm/ReadData/ToForm/… into it and copies the
# FORM binaries across. The plain `cp -r` above skips that step, so CalcFeynAmp
# dies with ReadForm::notcompiled (missing ReadForm) or "ToForm: No such file"
# (missing converters). Run ./compile here, then verify the layout LOUDLY.
log "Compiling FormCalc \$SystemID binaries (./compile)..."
SYSTEM_ID="$(
  "$WOLFRAM_BIN" -code 'WriteString["stdout", $SystemID]' 2>/dev/null \
  | tr -d '\r\n' || true
)"
WOLFRAM_INSTALL_DIR="$(
  "$WOLFRAM_BIN" -code 'WriteString["stdout", $InstallationDirectory]' 2>/dev/null \
  | tr -d '\r\n' || true
)"
if [ -z "$SYSTEM_ID" ] || [ -z "$WOLFRAM_INSTALL_DIR" ]; then
  blocker_json "FORMCALC_SMOKE_TEST_FAILED" "fatal" \
    "Could not determine Wolfram \$SystemID / \$InstallationDirectory; cannot compile FormCalc binaries" \
    '"user_instruction":"Check Wolfram Engine activation: run wolframscript --activate"'
  exit $EXIT_SMOKE
fi
log "Wolfram \$SystemID: $SYSTEM_ID"

TARGET_BIN_DIR="$APP_DIR/$SYSTEM_ID"
if [ ! -x "$TARGET_BIN_DIR/ReadForm" ] || [ ! -x "$TARGET_BIN_DIR/ToForm" ]; then
  # Primary lookup: the DeveloperKit path relative to $InstallationDirectory.
  # NB: on some layouts (e.g. WE 14.3, where $InstallationDirectory points
  # inside "Wolfram Player.app/Contents") this path does NOT exist and the
  # PATH fallback below is what actually resolves mcc — both are needed.
  # The ./compile C toolchain (mcc->cc, gfortran) is not pre-flighted; a
  # missing toolchain surfaces as the loud "./compile failed" blocker below.
  FC_MCC="$WOLFRAM_INSTALL_DIR/SystemFiles/Links/MathLink/DeveloperKit/$SYSTEM_ID/CompilerAdditions/mcc"
  FC_MATHKERNEL="$WOLFRAM_INSTALL_DIR/MacOS/MathKernel"
  if [ ! -x "$FC_MCC" ]; then
    # Fall back to mcc on PATH (mcc default in ./compile).
    FC_MCC="$(command -v mcc 2>/dev/null || true)"
  fi
  if [ -z "$FC_MCC" ] || [ ! -x "$FC_MCC" ]; then
    blocker_json "FORMCALC_SMOKE_TEST_FAILED" "fatal" \
      "MathLink compiler 'mcc' not found under $WOLFRAM_INSTALL_DIR; cannot compile ReadForm" \
      '"user_instruction":"Install the Wolfram MathLink DeveloperKit (ships with Wolfram Engine), then rerun _shared/installs/formcalc."'
    exit $EXIT_SMOKE
  fi
  # DEST=$SystemID bypasses ./compile's kernel-based $SystemID autodetection
  # (which cannot see an Engine nested inside Wolfram Player.app).
  COMPILE_LOG="$INSTALL_ROOT/formcalc_compile.log"
  if ! (
        cd "$APP_DIR" &&
        DEST="$SYSTEM_ID" MCC="$FC_MCC" MATH="$FC_MATHKERNEL" \
          PATH="$(dirname "$FC_MATHKERNEL"):$PATH" \
          ./compile
      ) > "$COMPILE_LOG" 2>&1; then
    blocker_json "FORMCALC_SMOKE_TEST_FAILED" "fatal" \
      "FormCalc ./compile failed; see $COMPILE_LOG" \
      "\"context\":{\"compile_log\":\"$COMPILE_LOG\"}"
    exit $EXIT_SMOKE
  fi
  log "Compiled FormCalc binaries into $TARGET_BIN_DIR"
fi

# Verification: FormCalc.m's exact lookup paths must resolve to executables.
# Fail the install loudly otherwise (this is the guard the layout regression
# would have tripped).
for _fcbin in ReadForm ToForm; do
  if [ ! -x "$TARGET_BIN_DIR/$_fcbin" ]; then
    blocker_json "FORMCALC_SMOKE_TEST_FAILED" "fatal" \
      "$TARGET_BIN_DIR/$_fcbin does not resolve to an executable (FormCalc.m would emit ReadForm::notcompiled / ToForm not found)" \
      '"user_instruction":"FormCalc install layout is broken; run FormCalc-9.10/compile manually, then rerun _shared/installs/formcalc."'
    exit $EXIT_SMOKE
  fi
done
log "Verified $TARGET_BIN_DIR/{ReadForm,ToForm} resolve."

# ── Step 8: Build LoopTools ───────────────────────────────────────────────────
LT_SRC_DIR=""
for d in "$FORMCALC_SRC_DIR"/LoopTools \
         "$FORMCALC_SRC_DIR"/looptools \
         "$INSTALL_ROOT"/FormCalc-*/LoopTools; do
  if [ -d "$d" ] && [ -f "$d/configure" ]; then
    LT_SRC_DIR="$d"
    break
  fi
done

LOOPTOOLS_LIB=""
LOOPTOOLS_QUAD_VAL="true"
if [ -n "$LT_SRC_DIR" ]; then
  log "Building LoopTools from $LT_SRC_DIR ..."
  LT_OUTPUT="$(bash "$SCRIPT_DIR/build_looptools.sh" "$LT_SRC_DIR" "$INSTALL_ROOT" "$LOOPTOOLS_VERSION")"
  # Parse key=value output
  while IFS='=' read -r k v; do
    case "$k" in
      looptools_lib)  LOOPTOOLS_LIB="$v" ;;
      looptools_quad) LOOPTOOLS_QUAD_VAL="$v" ;;
    esac
  done <<< "$LT_OUTPUT"
else
  warn "LoopTools source directory not found in FormCalc tarball. Skipping LoopTools build."
fi

# ── Step 9: Download + build FORM ─────────────────────────────────────────────
log "Building FORM ${FORM_VERSION}..."
FORM_BINARY="$(bash "$SCRIPT_DIR/build_form.sh" "$INSTALL_ROOT" "$FORM_VERSION")"
FORM_BINARY="${FORM_BINARY//[$'\r\n']/}"

# ── Step 10: Smoke test ────────────────────────────────────────────────────────
log "Running smoke test..."
SMOKE_RC=0
"$WOLFRAM_BIN" -script "$SCRIPT_DIR/smoke_test.wls" "$FORMCALC_PATH" "" || SMOKE_RC=$?
if [ "$SMOKE_RC" -ne 0 ]; then
  blocker_json "FORMCALC_SMOKE_TEST_FAILED" "fatal" \
    "FormCalc smoke test failed (exit $SMOKE_RC)" \
    '"user_instruction":"Check Wolfram Engine activation: run wolframscript --activate"'
  exit $EXIT_SMOKE
fi

# ── Step 11: config_merge ─────────────────────────────────────────────────────
INSTALLED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
config_merge \
  "formcalc_path" "$FORMCALC_PATH" \
  "formcalc_version" "$FORMCALC_VERSION" \
  "form_binary" "$FORM_BINARY" \
  "form_version" "$FORM_VERSION" \
  "looptools_lib" "${LOOPTOOLS_LIB:-}" \
  "looptools_version" "$LOOPTOOLS_VERSION" \
  "looptools_quad" "$LOOPTOOLS_QUAD_VAL" \
  "formcalc_installed_at" "$INSTALLED_AT"

log "FormCalc ${FORMCALC_VERSION} installed successfully."

# ── Check Wolfram activation ──────────────────────────────────────────────────
CHECK_ACTIVATION="$PLUGINS_DIR/shared/install-helpers/wolfram/check_wolfram_activation.sh"
if [ -f "$CHECK_ACTIVATION" ]; then
  ACTIVATION_JSON="$(bash "$CHECK_ACTIVATION" "$WOLFRAM_BIN" 2>/dev/null || true)"
  STATUS="$(printf '%s' "$ACTIVATION_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','ok'))" 2>/dev/null || echo 'ok')"
  if [ "$STATUS" = "activation_required" ]; then
    printf '{"status":"activation_required","message":"Wolfram Engine is installed but needs activation.","user_instruction":"Run `wolframscript --activate` in your terminal. Then rerun _shared/installs/formcalc."}\n'
    exit 0
  fi
fi

log "FormCalc is ready."
