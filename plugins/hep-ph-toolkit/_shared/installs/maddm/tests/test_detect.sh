#!/usr/bin/env bash
# test_detect.sh — Smoke tests for detect and use-path subcommands.
#
# Tests:
#   1. detect with no config → {"status":"missing"}, exit 0.
#   2. detect with madgraph_path pointing at an MG5 tree containing MadDM → "found".
#   3. detect with maddm_path configured → "configured" + version parsed.
#   4. use-path with bogus path → MADDM_PATH_INVALID blocker, non-zero exit.
#   5. use-path with a valid MadDM plugin dir → records maddm_path/version.
#
# All tests use isolated XDG_CONFIG_HOME so real user config is untouched.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../install.sh"
FIXTURES="$HERE/fixtures"

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

# Shared tmp root for isolation.
SHARED_TMP="$(mktemp -d -t hepph-maddm-install-XXXXXX)"
trap 'rm -rf "$SHARED_TMP"' EXIT

# Copy fixtures into writable tmp so we can freely `chmod` / `touch`.
cp -R "$FIXTURES/mg5_with_maddm" "$SHARED_TMP/"
cp -R "$FIXTURES/mg5_without_maddm" "$SHARED_TMP/"
chmod +x "$SHARED_TMP/mg5_with_maddm/bin/mg5_aMC" "$SHARED_TMP/mg5_with_maddm/bin/maddm" \
         "$SHARED_TMP/mg5_without_maddm/bin/mg5_aMC"

MG5_WITH="$SHARED_TMP/mg5_with_maddm"
MG5_WITHOUT="$SHARED_TMP/mg5_without_maddm"
MADDM_DIR="$MG5_WITH/PLUGIN/maddm"

# ---------------------------------------------------------------------------
# Test 1: detect with empty config → missing.
# ---------------------------------------------------------------------------
test_detect_missing() {
  local cfg_dir="$SHARED_TMP/cfg1"
  mkdir -p "$cfg_dir"
  local out exit_code=0
  out="$(XDG_CONFIG_HOME="$cfg_dir" bash "$SCRIPT" detect)" || exit_code=$?
  [ $exit_code -eq 0 ] || { printf '  ERROR: expected exit 0, got %d\n' "$exit_code"; return 1; }
  local status
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  [ "$status" = "missing" ] || { printf '  ERROR: expected status=missing, got %s\n' "$status"; return 1; }
  return 0
}

# ---------------------------------------------------------------------------
# Test 2: detect with madgraph_path but no maddm_path → scan finds plugin.
# ---------------------------------------------------------------------------
test_detect_found_via_scan() {
  local cfg_dir="$SHARED_TMP/cfg2"
  mkdir -p "$cfg_dir/hephaestus"
  python3 -c "
import json
with open('$cfg_dir/hephaestus/config.json', 'w') as f:
    json.dump({'madgraph_path': '$MG5_WITH/bin/mg5_aMC'}, f)
"
  local out status path
  out="$(XDG_CONFIG_HOME="$cfg_dir" bash "$SCRIPT" detect)"
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  [ "$status" = "found" ] || { printf '  ERROR: expected found, got %s (out=%s)\n' "$status" "$out"; return 1; }
  path="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("path",""))')"
  [ "$path" = "$MADDM_DIR" ] || { printf '  ERROR: expected path=%s, got %s\n' "$MADDM_DIR" "$path"; return 1; }
  return 0
}

# ---------------------------------------------------------------------------
# Test 3: detect with maddm_path configured → configured + version parsed.
# ---------------------------------------------------------------------------
test_detect_configured() {
  local cfg_dir="$SHARED_TMP/cfg3"
  mkdir -p "$cfg_dir/hephaestus"
  python3 -c "
import json
with open('$cfg_dir/hephaestus/config.json', 'w') as f:
    json.dump({
        'madgraph_path': '$MG5_WITH/bin/mg5_aMC',
        'maddm_path': '$MADDM_DIR',
    }, f)
"
  local out status version
  out="$(XDG_CONFIG_HOME="$cfg_dir" bash "$SCRIPT" detect)"
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  [ "$status" = "configured" ] || { printf '  ERROR: expected configured, got %s (out=%s)\n' "$status" "$out"; return 1; }
  version="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("version",""))')"
  [ "$version" = "3.2.13" ] || { printf '  ERROR: expected version=3.2.13, got %s\n' "$version"; return 1; }
  return 0
}

# ---------------------------------------------------------------------------
# Test 4: use-path with bogus path → MADDM_PATH_INVALID blocker, non-zero exit.
# ---------------------------------------------------------------------------
test_use_path_invalid() {
  local cfg_dir="$SHARED_TMP/cfg4"
  mkdir -p "$cfg_dir"
  local stderr_file="$SHARED_TMP/stderr4.txt"
  local exit_code=0
  XDG_CONFIG_HOME="$cfg_dir" bash "$SCRIPT" use-path "/nonexistent/path/to/maddm" \
    >/dev/null 2>"$stderr_file" || exit_code=$?
  [ $exit_code -ne 0 ] || { printf '  ERROR: expected non-zero exit, got 0\n'; return 1; }
  local code
  code="$(python3 -c "
import json, sys
line = open('$stderr_file').read().strip().splitlines()[-1] if open('$stderr_file').read().strip() else ''
if not line:
    sys.exit(1)
try:
    d = json.loads(line)
    print(d.get('code', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")"
  [ "$code" = "MADDM_PATH_INVALID" ] || {
    printf '  ERROR: expected MADDM_PATH_INVALID blocker, got code=%s\n' "$code"
    printf '  stderr was: %s\n' "$(cat "$stderr_file")"
    return 1
  }
  return 0
}

# ---------------------------------------------------------------------------
# Test 5: use-path with a valid MadDM plugin dir → records maddm_path/version.
# ---------------------------------------------------------------------------
test_use_path_valid() {
  local cfg_dir="$SHARED_TMP/cfg5"
  mkdir -p "$cfg_dir/hephaestus"
  # Seed madgraph_path so any downstream consumer can find MG5.
  python3 -c "
import json
with open('$cfg_dir/hephaestus/config.json', 'w') as f:
    json.dump({'madgraph_path': '$MG5_WITH/bin/mg5_aMC'}, f)
"
  local out status path version
  out="$(XDG_CONFIG_HOME="$cfg_dir" bash "$SCRIPT" use-path "$MADDM_DIR")"
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  [ "$status" = "configured" ] || { printf '  ERROR: expected configured, got %s\n' "$status"; return 1; }

  path="$(python3 -c "
import json
d = json.load(open('$cfg_dir/hephaestus/config.json'))
print(d.get('maddm_path', ''))
")"
  version="$(python3 -c "
import json
d = json.load(open('$cfg_dir/hephaestus/config.json'))
print(d.get('maddm_version', ''))
")"
  [ "$path" = "$MADDM_DIR" ] || { printf '  ERROR: maddm_path not recorded: got=%s\n' "$path"; return 1; }
  [ "$version" = "3.2.13" ] || { printf '  ERROR: maddm_version not recorded: got=%s\n' "$version"; return 1; }
  return 0
}

# ---------------------------------------------------------------------------
# Test 6: detect with no MadDM present under MG5 → missing (scan_candidates empty).
# ---------------------------------------------------------------------------
test_detect_mg5_without_maddm() {
  local cfg_dir="$SHARED_TMP/cfg6"
  mkdir -p "$cfg_dir/hephaestus"
  python3 -c "
import json
with open('$cfg_dir/hephaestus/config.json', 'w') as f:
    json.dump({'madgraph_path': '$MG5_WITHOUT/bin/mg5_aMC'}, f)
"
  local out status
  out="$(XDG_CONFIG_HOME="$cfg_dir" bash "$SCRIPT" detect)"
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
  [ "$status" = "missing" ] || { printf '  ERROR: expected missing, got %s\n' "$status"; return 1; }
  return 0
}

# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------
_run_test "detect: empty config -> missing"                       test_detect_missing
_run_test "detect: MG5 with MadDM, no maddm_path -> found"        test_detect_found_via_scan
_run_test "detect: maddm_path configured -> configured+version"   test_detect_configured
_run_test "use-path: bogus path -> MADDM_PATH_INVALID blocker"    test_use_path_invalid
_run_test "use-path: valid plugin dir -> records keys"            test_use_path_valid
_run_test "detect: MG5 without MadDM plugin -> missing"           test_detect_mg5_without_maddm

echo ""
printf 'Results: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
