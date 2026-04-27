#!/usr/bin/env bash
# Unit tests for install_wolfram.sh verify subcommand.
# Tests are isolated: each case creates a fresh mock wolframscript in a tmp dir.
# Run from the plugin root or any directory; uses absolute paths internally.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SCRIPT="$SCRIPT_DIR/../install_wolfram.sh"

pass() { printf 'PASS: %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

require_jq() {
  command -v jq >/dev/null 2>&1 || { printf 'SKIP: jq not found\n' >&2; exit 0; }
}
require_jq

TMPBASE="$(mktemp -d)"
cleanup() { rm -rf "$TMPBASE"; }
trap cleanup EXIT

make_mock() {
  # make_mock <dir> <name> <exit_code> <stdout_content>
  local dir="$1" name="$2" exit_code="$3" stdout_content="$4"
  mkdir -p "$dir"
  local script="$dir/$name"
  # Use a file to hold stdout content to avoid quoting issues
  local stdout_file="$TMPBASE/stdout_$$_${name}.txt"
  printf '%s' "$stdout_content" > "$stdout_file"
  cat > "$script" <<SCRIPT
#!/usr/bin/env bash
cat '$stdout_file'
exit ${exit_code}
SCRIPT
  chmod +x "$script"
  echo "$script"
}

# Override config to return empty path (no config file will exist in TMPBASE)
export XDG_CONFIG_HOME="$TMPBASE/config"

echo "=== test_verify_wolfram.sh ==="

# ── Case 1: happy path ────────────────────────────────────────────────────────
case1_dir="$TMPBASE/case1"
mock1="$(make_mock "$case1_dir" "wolframscript" 0 "$(printf '4\n14.1\n')")"
out1="$(bash "$INSTALL_SCRIPT" verify --path "$mock1")"
# wc -l counts newlines; command substitution strips trailing newline, so a
# single-line JSON (with or without trailing newline) shows 0 or 1 newlines.
[ "$(printf '%s' "$out1" | wc -l)" -le 1 ] || fail "case1: stdout must be exactly 1 line"
[ "$(printf '%s' "$out1" | jq -r '.ok')" = "true" ]          || fail "case1: ok != true"
[ "$(printf '%s' "$out1" | jq -r '.status')" = "ok" ]        || fail "case1: status != ok"
[ "$(printf '%s' "$out1" | jq -r '.tool')" = "wolfram" ]     || fail "case1: tool != wolfram"
[ "$(printf '%s' "$out1" | jq -r '.version')" = "14.1" ]     || fail "case1: version != 14.1"
[ "$(printf '%s' "$out1" | jq -r '.schema_version')" = "1" ] || fail "case1: schema_version != 1"
printf '%s' "$out1" | jq -e 'has("probe") | not' >/dev/null  || fail "case1: forbidden key 'probe' present"
printf '%s' "$out1" | jq -e 'has("expected_version") | not' >/dev/null || fail "case1: expected_version should be absent"
pass "case1: happy path"

# ── Case 2: activation banner ─────────────────────────────────────────────────
case2_dir="$TMPBASE/case2"
mock2="$(make_mock "$case2_dir" "wolframscript" 1 "$(printf 'Wolfram Engine requires activation. Please activate your license.\n')")"
out2_rc=0
out2="$(bash "$INSTALL_SCRIPT" verify --path "$mock2")" || out2_rc=$?
[ "$out2_rc" -ne 0 ] || fail "case2: should exit non-zero for broken install"
[ "$(printf '%s' "$out2" | jq -r '.status')" = "installed_broken" ] || fail "case2: status != installed_broken"
[ "$(printf '%s' "$out2" | jq -r '.hints[0].code')" = "wolfram_not_activated" ] || fail "case2: hint code != wolfram_not_activated"
pass "case2: activation banner"

# ── Case 3: exit 1 (generic failure) ─────────────────────────────────────────
case3_dir="$TMPBASE/case3"
mock3="$(make_mock "$case3_dir" "wolframscript" 1 "$(printf 'some error output\n')")"
out3_rc=0
out3="$(bash "$INSTALL_SCRIPT" verify --path "$mock3")" || out3_rc=$?
[ "$out3_rc" -ne 0 ] || fail "case3: should exit non-zero"
[ "$(printf '%s' "$out3" | jq -r '.status')" = "installed_broken" ] || fail "case3: status != installed_broken"
pass "case3: exit 1 generic failure"

# ── Case 4: missing path ──────────────────────────────────────────────────────
out4_rc=0
out4="$(bash "$INSTALL_SCRIPT" verify --path /does/not/exist)" || out4_rc=$?
[ "$out4_rc" -eq 16 ] || fail "case4: exit code should be 16, got $out4_rc"
[ "$(printf '%s' "$out4" | jq -r '.status')" = "missing" ] || fail "case4: status != missing"
pass "case4: missing path (exit 16)"

# ── Case 5: no path, no config ────────────────────────────────────────────────
out5_rc=0
out5="$(bash "$INSTALL_SCRIPT" verify)" || out5_rc=$?
[ "$out5_rc" -eq 17 ] || fail "case5: exit code should be 17, got $out5_rc"
[ "$(printf '%s' "$out5" | jq -r '.status')" = "not_configured" ] || fail "case5: status != not_configured"
pass "case5: no path no config (exit 17)"

# ── Case 6: strict version mismatch ──────────────────────────────────────────
case6_dir="$TMPBASE/case6"
mock6="$(make_mock "$case6_dir" "wolframscript" 0 "$(printf '4\n14.1.0 for MacOSX-ARM64\n')")"
out6_rc=0
out6="$(bash "$INSTALL_SCRIPT" verify --path "$mock6" --expected-version 14.2 --strict-version)" || out6_rc=$?
[ "$out6_rc" -ne 0 ] || fail "case6: should exit non-zero on strict mismatch"
[ "$(printf '%s' "$out6" | jq -r '.status')" = "version_mismatch" ] || fail "case6: status != version_mismatch"
[ "$(printf '%s' "$out6" | jq -r '.ok')" = "false" ] || fail "case6: ok should be false"
pass "case6: strict version mismatch (exit 15)"

# ── Case 7: non-strict drift ─────────────────────────────────────────────────
case7_dir="$TMPBASE/case7"
mock7="$(make_mock "$case7_dir" "wolframscript" 0 "$(printf '4\n14.1.0 for MacOSX-ARM64\n')")"
out7_rc=0
out7="$(bash "$INSTALL_SCRIPT" verify --path "$mock7" --expected-version 14.2)" || out7_rc=$?
[ "$out7_rc" -eq 0 ] || fail "case7: should exit 0 on non-strict drift, got $out7_rc"
[ "$(printf '%s' "$out7" | jq -r '.ok')" = "true" ] || fail "case7: ok should be true on non-strict drift"
detail7="$(printf '%s' "$out7" | jq -r '.detail')"
printf '%s' "$detail7" | grep -q "14.1" || fail "case7: detail should mention found version 14.1"
printf '%s' "$detail7" | grep -q "14.2" || fail "case7: detail should mention expected version 14.2"
pass "case7: non-strict drift (ok=true, detail has both versions)"

# ── Case 8: timeout ───────────────────────────────────────────────────────────
case8_dir="$TMPBASE/case8"
mock8_script="$case8_dir/wolframscript"
mkdir -p "$case8_dir"
cat > "$mock8_script" <<'SCRIPT'
#!/usr/bin/env bash
sleep 30
SCRIPT
chmod +x "$mock8_script"
out8_rc=0
out8="$(bash "$INSTALL_SCRIPT" verify --path "$mock8_script" --timeout 2)" || out8_rc=$?
[ "$out8_rc" -ne 0 ] || fail "case8: should exit non-zero on timeout"
[ "$(printf '%s' "$out8" | jq -r '.status')" = "timeout" ] || fail "case8: status != timeout, got: $(printf '%s' "$out8" | jq -r '.status')"
pass "case8: timeout (status=timeout)"

# ── Case 9: rc=0 but version line is unparseable (e.g. "Null") ───────────────
case9_dir="$TMPBASE/case9"
mock9="$(make_mock "$case9_dir" "wolframscript" 0 "$(printf '4\nNull\n')")"
out9_rc=0
out9="$(bash "$INSTALL_SCRIPT" verify --path "$mock9")" || out9_rc=$?
[ "$out9_rc" -eq 15 ] || fail "case9: exit code should be 15 (installed_broken), got $out9_rc"
[ "$(printf '%s' "$out9" | wc -l)" -le 1 ] || fail "case9: stdout must be exactly 1 line"
[ "$(printf '%s' "$out9" | jq -r '.ok')" = "false" ]                    || fail "case9: ok should be false"
[ "$(printf '%s' "$out9" | jq -r '.status')" = "installed_broken" ]     || fail "case9: status != installed_broken"
pass "case9: rc=0 with Null version → installed_broken (exit 15)"

# ── Global schema invariants ──────────────────────────────────────────────────
for out in "$out1" "$out2" "$out3" "$out4" "$out5" "$out6" "$out7" "$out8" "$out9"; do
  [ "$(printf '%s' "$out" | jq -r '.schema_version')" = "1" ] || fail "schema_version != 1 in one of the outputs"
  [ "$(printf '%s' "$out" | jq -r '.tool')" = "wolfram" ]     || fail "tool != wolfram in one of the outputs"
  printf '%s' "$out" | jq -e 'has("probe") | not' >/dev/null  || fail "forbidden key 'probe' present in one of the outputs"
done
pass "global: schema_version=1, tool=wolfram, no 'probe' key in all outputs"

echo "=== ALL CASES PASSED ==="
