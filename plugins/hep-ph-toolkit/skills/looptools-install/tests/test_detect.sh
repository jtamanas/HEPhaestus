#!/usr/bin/env bash
# test_detect.sh — smoke tests for /looptools-install.
#
# Tests:
#   1. detect with no config → {"status":"missing"}, exit 0.
#   2. detect with looptools_path configured → {"status":"configured", ...}.
#   3. use-path with non-existent prefix → fatal blocker, non-zero exit.
#   4. use-path with prefix lacking libooptools.a → fatal blocker.
#   5. use-path with fixture stub (has all markers) → records config, exit 0.
#      Skipped if gfortran is not on PATH (use-path requires gfortran to
#      record looptools_gfortran_version).
#   6. validate with configured path → exit 0, prints {"status":"ok",...}.
#   7. probe_looptools.sh light mode on stub → exit 0.
#   8. probe_looptools.sh light mode on empty dir → fatal blocker.
#
# All tests isolate XDG_CONFIG_HOME.
set -euo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$TEST_DIR/../scripts/install.sh"
PROBE="$TEST_DIR/../scripts/probe_looptools.sh"
FIXTURE="$TEST_DIR/fixtures/looptools_stub/LoopTools-2.16"

pass=0
fail=0

_run_test() {
  local name="$1"
  local fn="$2"
  if "$fn"; then
    printf '[PASS] %s\n' "$name"
    pass=$((pass + 1))
  else
    printf '[FAIL] %s\n' "$name"
    fail=$((fail + 1))
  fi
}

SHARED_TMP="$(mktemp -d -t hepph-lt-XXXXXX)"
trap 'rm -rf "$SHARED_TMP"' EXIT

# ---------------------------------------------------------------------------
# Test 1: detect → missing
# ---------------------------------------------------------------------------
test_detect_missing() {
  local cfg_dir="$SHARED_TMP/cfg1"
  mkdir -p "$cfg_dir"
  # Use a non-standard HOME so scan_candidates doesn't find anything real.
  local out
  out="$(HOME="$SHARED_TMP/empty_home" XDG_CONFIG_HOME="$cfg_dir" \
    bash "$SCRIPT" detect)"
  local status
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  [ "$status" = "missing" ] || { printf '  ERROR: expected missing, got %s\n' "$status"; return 1; }
  return 0
}

# ---------------------------------------------------------------------------
# Test 2: detect with looptools_path configured.
# ---------------------------------------------------------------------------
test_detect_configured() {
  local cfg_dir="$SHARED_TMP/cfg2"
  mkdir -p "$cfg_dir/hephaestus"
  python3 -c "
import json
cfg = '$cfg_dir/hephaestus/config.json'
json.dump({
    'looptools_path': '$FIXTURE',
    'looptools_version': '2.16',
    'looptools_gfortran_version': 'GNU Fortran test 13.0.0',
}, open(cfg, 'w'))
"
  local out
  out="$(XDG_CONFIG_HOME="$cfg_dir" bash "$SCRIPT" detect)"
  local status path
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  path="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["path"])')"
  [ "$status" = "configured" ] || { printf '  ERROR: status=%s\n' "$status"; return 1; }
  [ "$path" = "$FIXTURE" ] || { printf '  ERROR: path=%s\n' "$path"; return 1; }
  return 0
}

# ---------------------------------------------------------------------------
# Test 3: use-path with non-existent prefix → blocker.
# ---------------------------------------------------------------------------
test_use_path_nonexistent() {
  local cfg_dir="$SHARED_TMP/cfg3"
  mkdir -p "$cfg_dir"
  local stderr_file="$SHARED_TMP/stderr3.txt"
  local exit_code=0
  XDG_CONFIG_HOME="$cfg_dir" bash "$SCRIPT" use-path "/nonexistent/lt/prefix" \
    >/dev/null 2>"$stderr_file" || exit_code=$?
  [ $exit_code -ne 0 ] || { printf '  ERROR: expected non-zero exit\n'; return 1; }
  local code
  code="$(python3 -c "
import json, sys
for line in open('$stderr_file'):
    line=line.strip()
    if not line.startswith('{'): continue
    try:
        d=json.loads(line)
        print(d['code']); break
    except Exception: pass
" 2>/dev/null || echo "")"
  [ "$code" = "LOOPTOOLS_PATH_INVALID" ] || {
    printf '  ERROR: expected LOOPTOOLS_PATH_INVALID, got %s. stderr:\n%s\n' "$code" "$(cat "$stderr_file")"
    return 1
  }
  return 0
}

# ---------------------------------------------------------------------------
# Test 4: use-path with directory but no libooptools.a → blocker.
# ---------------------------------------------------------------------------
test_use_path_invalid_prefix() {
  local cfg_dir="$SHARED_TMP/cfg4"
  local empty_prefix="$SHARED_TMP/empty_prefix"
  mkdir -p "$cfg_dir" "$empty_prefix"
  local stderr_file="$SHARED_TMP/stderr4.txt"
  local exit_code=0
  XDG_CONFIG_HOME="$cfg_dir" bash "$SCRIPT" use-path "$empty_prefix" \
    >/dev/null 2>"$stderr_file" || exit_code=$?
  [ $exit_code -ne 0 ] || { printf '  ERROR: expected non-zero exit\n'; return 1; }
  grep -q 'LOOPTOOLS_PATH_INVALID' "$stderr_file" || {
    printf '  ERROR: expected LOOPTOOLS_PATH_INVALID in stderr. got:\n%s\n' "$(cat "$stderr_file")"
    return 1
  }
  return 0
}

# ---------------------------------------------------------------------------
# Test 5: use-path with fixture stub → records config.
# Skipped if gfortran absent.
# ---------------------------------------------------------------------------
test_use_path_fixture() {
  if ! command -v gfortran >/dev/null 2>&1; then
    printf '  SKIP: gfortran not present, skipping use-path fixture test\n'
    return 0
  fi
  local cfg_dir="$SHARED_TMP/cfg5"
  mkdir -p "$cfg_dir"
  local out
  out="$(XDG_CONFIG_HOME="$cfg_dir" bash "$SCRIPT" use-path "$FIXTURE")"
  local status
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  [ "$status" = "configured" ] || { printf '  ERROR: status=%s\n' "$status"; return 1; }

  # Verify keys written.
  local got_path got_gf_ver got_gf_path
  got_path="$(python3 -c "import json; print(json.load(open('$cfg_dir/hephaestus/config.json'))['looptools_path'])")"
  got_gf_ver="$(python3 -c "import json; print(json.load(open('$cfg_dir/hephaestus/config.json'))['looptools_gfortran_version'])")"
  got_gf_path="$(python3 -c "import json; print(json.load(open('$cfg_dir/hephaestus/config.json'))['looptools_gfortran_path'])")"
  [ "$got_path" = "$FIXTURE" ] || { printf '  ERROR: looptools_path=%s\n' "$got_path"; return 1; }
  [ -n "$got_gf_ver" ] || { printf '  ERROR: looptools_gfortran_version empty\n'; return 1; }
  [ -n "$got_gf_path" ] || { printf '  ERROR: looptools_gfortran_path empty\n'; return 1; }
  return 0
}

# ---------------------------------------------------------------------------
# Test 6: validate on a configured path.
# ---------------------------------------------------------------------------
test_validate_ok() {
  local cfg_dir="$SHARED_TMP/cfg6"
  mkdir -p "$cfg_dir/hephaestus"
  python3 -c "
import json
json.dump({'looptools_path': '$FIXTURE'}, open('$cfg_dir/hephaestus/config.json', 'w'))
"
  local out
  out="$(XDG_CONFIG_HOME="$cfg_dir" bash "$SCRIPT" validate)"
  local status
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  [ "$status" = "ok" ] || { printf '  ERROR: expected ok, got %s\n' "$status"; return 1; }
  return 0
}

# ---------------------------------------------------------------------------
# Test 7: probe light mode on fixture.
# ---------------------------------------------------------------------------
test_probe_light_ok() {
  local out
  out="$(bash "$PROBE" "$FIXTURE")"
  local status mode
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  mode="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["mode"])')"
  [ "$status" = "ok" ] || { printf '  ERROR: status=%s\n' "$status"; return 1; }
  [ "$mode" = "light" ] || { printf '  ERROR: mode=%s\n' "$mode"; return 1; }
  return 0
}

# ---------------------------------------------------------------------------
# Test 8: probe light mode on empty dir → blocker + exit 15.
# ---------------------------------------------------------------------------
test_probe_light_fail() {
  local empty="$SHARED_TMP/empty_probe"
  mkdir -p "$empty"
  local stderr_file="$SHARED_TMP/stderr8.txt"
  local exit_code=0
  bash "$PROBE" "$empty" >/dev/null 2>"$stderr_file" || exit_code=$?
  [ "$exit_code" -eq 15 ] || { printf '  ERROR: expected exit 15, got %d\n' "$exit_code"; return 1; }
  grep -q 'LOOPTOOLS_SMOKE_TEST_FAILED' "$stderr_file" || {
    printf '  ERROR: missing blocker code. stderr:\n%s\n' "$(cat "$stderr_file")"
    return 1
  }
  return 0
}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
_run_test "detect: empty config → missing"                     test_detect_missing
_run_test "detect: configured path → configured"               test_detect_configured
_run_test "use-path: non-existent prefix → blocker"            test_use_path_nonexistent
_run_test "use-path: dir without libooptools.a → blocker"      test_use_path_invalid_prefix
_run_test "use-path: fixture stub → records config"            test_use_path_fixture
_run_test "validate: configured fixture → ok"                  test_validate_ok
_run_test "probe: light mode on fixture → ok"                  test_probe_light_ok
_run_test "probe: light mode on empty dir → blocker+exit15"    test_probe_light_fail

echo ""
printf 'Results: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
