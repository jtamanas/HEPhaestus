#!/usr/bin/env bash
# test_cmd_detect_activation.sh — T8 unit test for cmd_detect activation_required branch.
#
# 5-step spec (LOCKED — ws4_plan_final.md §9 item 4):
# 1. Source install.sh so cmd_detect and helpers are in scope.
# 2. Stub config_get, wolfram_path, is_drake_dir, run_smoke by exporting shell functions.
# 3. Drive 3 cases: ok→configured, activation_required→activation_required, error→found.
# 4. Each case: capture stdout, parse via python -c json.load, assert d['status'] == expected.
# 5. Exit 0 only if all three pass; print "OK 3/3 cases" on success.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SH="$SCRIPT_DIR/../install.sh"

PASS=0
FAIL=0

# ---------------------------------------------------------------------------
# Helper: run one case in a subshell with stubbed dependencies
# ---------------------------------------------------------------------------
run_case() {
  local case_name="$1"
  local smoke_status="$2"
  local expected_status="$3"

  # Run in a subshell so stub exports don't leak
  local result
  result=$(bash -c "
set -euo pipefail
# Provide minimal _common.sh stubs that install.sh sources
# We override SHARED_COMMON to a no-op file
_TMPDIR=\$(mktemp -d)
printf '#!/bin/bash\n# no-op common stub\nconfig_get() { echo \"\"; }\nlog() { :; }\nwarn() { :; }\nerr() { :; }\nemit_blocker() { :; }\ncheck_disk() { :; }\nverify_checksum() { :; }\ndownload_with_retry() { :; }\n# exit codes\nEXIT_BAD_PATH=3\nEXIT_NO_WOLFRAM=4\nEXIT_SMOKE=5\nEXIT_NO_UNZIP=6\nEXIT_EXTRACT=7\n' > \"\$_TMPDIR/_common.sh\"
printf '#!/bin/bash\n# no-op blocker stub\nemit_blocker() { :; }\n' > \"\$_TMPDIR/_blocker.sh\"

# Source install.sh with SHARED_COMMON pointed at our stub
# We need to override functions AFTER sourcing
SHARED_COMMON=\"\$_TMPDIR/_common.sh\"
source \"\$_TMPDIR/_common.sh\"
source \"\$_TMPDIR/_blocker.sh\"

# Now override the 4 functions cmd_detect calls:
# config_get drake_path → return a temp dir (non-empty, so branch2 fires)
_DRAKE_TMP=\"\$_TMPDIR/fake_drake\"
mkdir -p \"\$_DRAKE_TMP/test\"
touch \"\$_DRAKE_TMP/test/test.wls\"
config_get() { echo \"\$_DRAKE_TMP\"; }
wolfram_path() { echo '/usr/local/bin/wolframscript'; }
is_drake_dir() { return 0; }
run_smoke() { printf '{\"status\":\"$smoke_status\"}\n'; }

# Source the functions we need from install.sh (skip main execution)
# We do this by extracting cmd_detect using sed
$(sed -n '/^cmd_detect()/,/^}/p' "$INSTALL_SH")

# Run cmd_detect
cmd_detect
" 2>/dev/null)

  local actual_status
  actual_status=$(printf '%s' "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['status'])" 2>/dev/null || echo "PARSE_ERROR")

  if [ "$actual_status" = "$expected_status" ]; then
    echo "PASS: $case_name → status=$actual_status"
    PASS=$((PASS + 1))
  else
    echo "FAIL: $case_name → expected status=$expected_status, got status=$actual_status (raw: $result)"
    FAIL=$((FAIL + 1))
  fi
}

# ---------------------------------------------------------------------------
# Case (a): smoke status=ok → cmd_detect emits configured
# ---------------------------------------------------------------------------
run_case "ok→configured" "ok" "configured"

# ---------------------------------------------------------------------------
# Case (b): smoke status=activation_required → cmd_detect emits activation_required
# ---------------------------------------------------------------------------
run_case "activation_required→activation_required" "activation_required" "activation_required"

# ---------------------------------------------------------------------------
# Case (c): smoke status=error → cmd_detect emits found (falls through)
# ---------------------------------------------------------------------------
run_case "error→found" "error" "found"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
TOTAL=$((PASS + FAIL))
if [ "$FAIL" -eq 0 ]; then
  echo "OK 3/3 cases"
  exit 0
else
  echo "FAIL: $FAIL/$TOTAL cases failed"
  exit 1
fi
