#!/usr/bin/env bash
# test_detect_derive_src.sh — Smoke tests for detect and use-path subcommands.
#
# Tests:
#   1. detect with no config → {"status":"missing"}, exit 0.
#   2. detect with spheno_path in config → reports spheno_src_path correctly.
#   3. use-path with non-existent path → fatal blocker on stderr, non-zero exit.
#   4. use-path with a fake binary → records both spheno_path and spheno_src_path.
#   5. use-path with a fake source tree dir → records both keys.
#
# All tests use isolated HEPPH_STATE_ROOT and XDG_CONFIG_HOME.
set -euo pipefail

SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/install.sh"

pass=0
fail=0

_run_test() {
  local name="$1"
  local fn="$2"
  if "$fn" 2>/tmp/hepph_test_stderr_$$.txt; then
    printf '[PASS] %s\n' "$name"
    (( pass++ )) || true
  else
    printf '[FAIL] %s\n' "$name"
    (( fail++ )) || true
  fi
}

# ---------------------------------------------------------------------------
# Setup shared tmp root for all tests (cleaned on EXIT).
# ---------------------------------------------------------------------------
SHARED_TMP="$(mktemp -d -t hepph-w2-XXXXXX)"
trap 'rm -rf "$SHARED_TMP"' EXIT

# ---------------------------------------------------------------------------
# Test 1: detect with empty config → missing.
# ---------------------------------------------------------------------------
test_detect_missing() {
  local cfg_dir="$SHARED_TMP/cfg1"
  local state_dir="$SHARED_TMP/state1"
  local fake_home="$SHARED_TMP/home1"
  mkdir -p "$cfg_dir" "$state_dir" "$fake_home"

  # Isolate HOME so scan_candidates doesn't find the real user install.
  local out
  out="$(HOME="$fake_home" XDG_CONFIG_HOME="$cfg_dir" HEPPH_STATE_ROOT="$state_dir" \
    bash "$SCRIPT" detect)"
  local exit_code=$?

  [ $exit_code -eq 0 ] || { printf '  ERROR: exit code was %d\n' "$exit_code"; return 1; }

  # Output must be {"status":"missing"}
  local status
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["status"])')"
  [ "$status" = "missing" ] || { printf '  ERROR: expected status=missing, got %s\n' "$status"; return 1; }
  return 0
}

# ---------------------------------------------------------------------------
# Test 2: detect with spheno_path configured → configured + src_path derived.
#         Also asserts that detect now persists the derived spheno_src_path
#         into config (caching promotion), while spheno_version is NOT
#         persisted (re-probed on every cmd_install to keep version-mismatch
#         honest).
# ---------------------------------------------------------------------------
test_detect_configured_with_src() {
  local cfg_dir="$SHARED_TMP/cfg2"
  local state_dir="$SHARED_TMP/state2"
  local fake_root="$SHARED_TMP/fake_spheno_2/SPheno-4.0.5"
  mkdir -p "$cfg_dir/hephaestus" "$state_dir" "$fake_root/bin"

  # Create a fake executable binary at the expected path.
  local fake_bin="$fake_root/bin/SPheno"
  printf '#!/usr/bin/env bash\necho "SPheno v4.0.5 usage: provide LesHouches input"\n' > "$fake_bin"
  chmod +x "$fake_bin"
  # Create Makefile so src derivation works.
  touch "$fake_root/Makefile"

  # Write a minimal config.json with spheno_path set.
  python3 -c "
import json, os
cfg = '$cfg_dir/hephaestus/config.json'
os.makedirs(os.path.dirname(cfg), exist_ok=True)
with open(cfg, 'w') as f:
    json.dump({'spheno_path': '$fake_bin'}, f)
"

  local out
  out="$(XDG_CONFIG_HOME="$cfg_dir" HEPPH_STATE_ROOT="$state_dir" \
    bash "$SCRIPT" detect)"

  local status src_path
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["status"])')"
  [ "$status" = "configured" ] || { printf '  ERROR: expected configured, got %s\n' "$status"; return 1; }

  src_path="$(printf '%s' "$out" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("src_path",""))')"
  # src_path should be the directory containing Makefile (fake_root).
  [ "$src_path" = "$fake_root" ] || {
    printf '  ERROR: expected src_path=%s, got %s\n' "$fake_root" "$src_path"
    return 1
  }

  # NEW: detect must also persist the derived spheno_src_path into config.
  local cfg_src_path cfg_has_version
  cfg_src_path="$(python3 -c "
import json
cfg = '$cfg_dir/hephaestus/config.json'
d = json.load(open(cfg))
print(d.get('spheno_src_path', ''))
")"
  [ "$cfg_src_path" = "$fake_root" ] || {
    printf '  ERROR: detect did not persist spheno_src_path to config (got=%s expected=%s)\n' "$cfg_src_path" "$fake_root"
    return 1
  }

  # NEW: detect must NOT persist spheno_version (cmd_install re-probes it).
  cfg_has_version="$(python3 -c "
import json
cfg = '$cfg_dir/hephaestus/config.json'
d = json.load(open(cfg))
print('yes' if 'spheno_version' in d else 'no')
")"
  [ "$cfg_has_version" = "no" ] || {
    printf '  ERROR: detect persisted spheno_version to config (should be re-probed on every install)\n'
    return 1
  }
  return 0
}

# ---------------------------------------------------------------------------
# Test 2b: detect with stale spheno_src_path in config (Makefile missing) →
#          falls through to derive and repersists the fresh derived path.
# ---------------------------------------------------------------------------
test_detect_stale_src_path_in_config() {
  local cfg_dir="$SHARED_TMP/cfg2b"
  local state_dir="$SHARED_TMP/state2b"
  local fake_root="$SHARED_TMP/fake_spheno_2b/SPheno-4.0.5"
  local stale_src="$SHARED_TMP/stale_spheno_2b/SPheno-4.0.5"
  mkdir -p "$cfg_dir/hephaestus" "$state_dir" "$fake_root/bin"

  local fake_bin="$fake_root/bin/SPheno"
  printf '#!/usr/bin/env bash\necho "SPheno usage: LesHouches"\n' > "$fake_bin"
  chmod +x "$fake_bin"
  touch "$fake_root/Makefile"

  # Write config that points spheno_src_path at a path that no longer exists.
  python3 -c "
import json, os
cfg = '$cfg_dir/hephaestus/config.json'
os.makedirs(os.path.dirname(cfg), exist_ok=True)
with open(cfg, 'w') as f:
    json.dump({'spheno_path': '$fake_bin', 'spheno_src_path': '$stale_src'}, f)
"

  local out
  out="$(XDG_CONFIG_HOME="$cfg_dir" HEPPH_STATE_ROOT="$state_dir" \
    bash "$SCRIPT" detect)"

  local src_path
  src_path="$(printf '%s' "$out" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("src_path",""))')"
  [ "$src_path" = "$fake_root" ] || {
    printf '  ERROR: stale src_path not re-derived; got %s\n' "$src_path"
    return 1
  }

  # Config must now contain the fresh derived path, not the stale one.
  local cfg_src
  cfg_src="$(python3 -c "
import json
cfg = '$cfg_dir/hephaestus/config.json'
print(json.load(open(cfg)).get('spheno_src_path', ''))
")"
  [ "$cfg_src" = "$fake_root" ] || {
    printf '  ERROR: config still has stale src_path=%s (expected %s)\n' "$cfg_src" "$fake_root"
    return 1
  }
  return 0
}

# ---------------------------------------------------------------------------
# Test 3: use-path with non-existent path → fatal blocker + non-zero exit.
# ---------------------------------------------------------------------------
test_use_path_nonexistent() {
  local cfg_dir="$SHARED_TMP/cfg3"
  local state_dir="$SHARED_TMP/state3"
  mkdir -p "$cfg_dir" "$state_dir"

  local stderr_file="$SHARED_TMP/stderr3.txt"
  local exit_code=0

  XDG_CONFIG_HOME="$cfg_dir" HEPPH_STATE_ROOT="$state_dir" \
    bash "$SCRIPT" use-path "/nonexistent/path/bin/SPheno" \
    >/dev/null 2>"$stderr_file" || exit_code=$?

  # Must exit with non-zero (EXIT_BAD_PATH = 16).
  [ $exit_code -ne 0 ] || { printf '  ERROR: expected non-zero exit, got 0\n'; return 1; }

  # Stderr must contain a blocker JSON with code=SPHENO_PATH_INVALID.
  local code
  code="$(python3 -c "
import json, sys
line = open('$stderr_file').read().strip()
if not line:
    sys.exit(1)
d = json.loads(line)
print(d['code'])
" 2>/dev/null || echo "")"
  [ "$code" = "SPHENO_PATH_INVALID" ] || {
    printf '  ERROR: expected SPHENO_PATH_INVALID blocker, got code=%s\n' "$code"
    printf '  stderr was: %s\n' "$(cat "$stderr_file")"
    return 1
  }
  return 0
}

# ---------------------------------------------------------------------------
# Test 4: use-path with a fake binary → records both keys.
# ---------------------------------------------------------------------------
test_use_path_binary() {
  local cfg_dir="$SHARED_TMP/cfg4"
  local state_dir="$SHARED_TMP/state4"
  local fake_root="$SHARED_TMP/fake_spheno_4/SPheno-4.0.5"
  mkdir -p "$cfg_dir/hephaestus" "$state_dir" "$fake_root/bin"

  local fake_bin="$fake_root/bin/SPheno"
  # Fake binary emits smoke-test-passable output.
  printf '#!/usr/bin/env bash\necho "SPheno usage: provide LesHouches input file"\n' > "$fake_bin"
  chmod +x "$fake_bin"
  touch "$fake_root/Makefile"

  local out
  out="$(XDG_CONFIG_HOME="$cfg_dir" HEPPH_STATE_ROOT="$state_dir" \
    bash "$SCRIPT" use-path "$fake_bin")"

  local status spheno_path spheno_src_path
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["status"])')"
  [ "$status" = "configured" ] || { printf '  ERROR: expected configured, got %s\n' "$status"; return 1; }

  # Verify both keys are in config.json.
  spheno_path="$(XDG_CONFIG_HOME="$cfg_dir" python3 -c "
import json, os
cfg = '$cfg_dir/hephaestus/config.json'
d = json.load(open(cfg))
print(d.get('spheno_path', ''))
")"
  spheno_src_path="$(XDG_CONFIG_HOME="$cfg_dir" python3 -c "
import json, os
cfg = '$cfg_dir/hephaestus/config.json'
d = json.load(open(cfg))
print(d.get('spheno_src_path', ''))
")"

  [ "$spheno_path" = "$fake_bin" ] || {
    printf '  ERROR: spheno_path not set correctly: %s\n' "$spheno_path"; return 1
  }
  [ "$spheno_src_path" = "$fake_root" ] || {
    printf '  ERROR: spheno_src_path not set correctly: got=%s expected=%s\n' "$spheno_src_path" "$fake_root"
    return 1
  }
  return 0
}

# ---------------------------------------------------------------------------
# Test 5: use-path with a source tree directory → records both keys.
# ---------------------------------------------------------------------------
test_use_path_source_tree() {
  local cfg_dir="$SHARED_TMP/cfg5"
  local state_dir="$SHARED_TMP/state5"
  local fake_root="$SHARED_TMP/fake_spheno_5/SPheno-4.0.5"
  mkdir -p "$cfg_dir/hephaestus" "$state_dir" "$fake_root/bin"

  local fake_bin="$fake_root/bin/SPheno"
  printf '#!/usr/bin/env bash\necho "LesHouches input file required"\n' > "$fake_bin"
  chmod +x "$fake_bin"
  touch "$fake_root/Makefile"

  local out
  out="$(XDG_CONFIG_HOME="$cfg_dir" HEPPH_STATE_ROOT="$state_dir" \
    bash "$SCRIPT" use-path "$fake_root")"

  local status spheno_path spheno_src_path
  status="$(printf '%s' "$out" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["status"])')"
  [ "$status" = "configured" ] || { printf '  ERROR: expected configured, got %s\n' "$status"; return 1; }

  spheno_path="$(python3 -c "
import json
cfg = '$cfg_dir/hephaestus/config.json'
d = json.load(open(cfg))
print(d.get('spheno_path', ''))
")"
  spheno_src_path="$(python3 -c "
import json
cfg = '$cfg_dir/hephaestus/config.json'
d = json.load(open(cfg))
print(d.get('spheno_src_path', ''))
")"

  [ "$spheno_path" = "$fake_bin" ] || {
    printf '  ERROR: spheno_path not set: got=%s expected=%s\n' "$spheno_path" "$fake_bin"
    return 1
  }
  [ "$spheno_src_path" = "$fake_root" ] || {
    printf '  ERROR: spheno_src_path not set: got=%s expected=%s\n' "$spheno_src_path" "$fake_root"
    return 1
  }
  return 0
}

# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------
_run_test "detect: empty config → missing"       test_detect_missing
_run_test "detect: spheno_path in config → src_path derived + persisted" test_detect_configured_with_src
_run_test "detect: stale src_path (Makefile missing) → re-derived + repersisted" test_detect_stale_src_path_in_config
_run_test "use-path: non-existent path → fatal blocker" test_use_path_nonexistent
_run_test "use-path: binary form → records both keys" test_use_path_binary
_run_test "use-path: source tree form → records both keys" test_use_path_source_tree

echo ""
printf 'Results: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
