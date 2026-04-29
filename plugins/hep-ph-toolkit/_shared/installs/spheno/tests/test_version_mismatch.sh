#!/usr/bin/env bash
# test_version_mismatch.sh — Smoke test for version-mismatch → install-fresh-alongside path.
#
# Strategy: set up a fake existing install at version 9.9.9 and set HEPPH_SPHENO_VERSION=4.0.5.
# Stub curl so no network is needed. The test asserts that the install subcommand
# emits the version_mismatch JSON status before attempting the fresh install.
#
# We only test the decision logic, not the full compile. The stub curl returns a
# non-zero exit code to abort after the mismatch announcement is verified.
set -euo pipefail

SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/install.sh"

pass=0
fail=0

_run_test() {
  local name="$1"
  local fn="$2"
  if "$fn" 2>/tmp/hepph_vmtest_stderr_$$.txt; then
    printf '[PASS] %s\n' "$name"
    (( pass++ )) || true
  else
    printf '[FAIL] %s\n' "$name"
    (( fail++ )) || true
  fi
}

SHARED_TMP="$(mktemp -d -t hepph-vmtest-XXXXXX)"
trap 'rm -rf "$SHARED_TMP"' EXIT

# ---------------------------------------------------------------------------
# Test 1: Version mismatch triggers install_fresh_alongside announcement.
# ---------------------------------------------------------------------------
test_version_mismatch_announcement() {
  local cfg_dir="$SHARED_TMP/cfg_vm1"
  local state_dir="$SHARED_TMP/state_vm1"

  # Build a fake SPheno install at version "9.9.9" in a versioned subdirectory.
  local fake_root="$SHARED_TMP/SPheno-9.9.9"
  mkdir -p "$cfg_dir/hephaestus" "$state_dir" "$fake_root/bin"

  local fake_bin="$fake_root/bin/SPheno"
  printf '#!/usr/bin/env bash\necho "LesHouches input file required"\n' > "$fake_bin"
  chmod +x "$fake_bin"
  touch "$fake_root/Makefile"

  # Write config with spheno_path pointing to the fake 9.9.9 install.
  python3 -c "
import json, os
cfg = '$cfg_dir/hephaestus/config.json'
os.makedirs(os.path.dirname(cfg), exist_ok=True)
with open(cfg, 'w') as f:
    json.dump({'spheno_path': '$fake_bin', 'spheno_version': '9.9.9'}, f)
"

  # Create a fake curl stub that immediately fails (simulates no network).
  # This means install will abort after the mismatch is announced.
  local fake_bin_dir="$SHARED_TMP/fakepath_vm1"
  mkdir -p "$fake_bin_dir"
  printf '#!/usr/bin/env bash\nexit 1\n' > "$fake_bin_dir/curl"
  chmod +x "$fake_bin_dir/curl"

  # Run install with pin=4.0.5, existing=9.9.9.
  # Capture stdout; expect version_mismatch before the download failure.
  local stdout_file="$SHARED_TMP/stdout_vm1.txt"
  local exit_code=0
  PATH="$fake_bin_dir:$PATH" \
    XDG_CONFIG_HOME="$cfg_dir" \
    HEPPH_STATE_ROOT="$state_dir" \
    HEPPH_SPHENO_VERSION="4.0.5" \
    bash "$SCRIPT" install \
    >"$stdout_file" 2>/dev/null || exit_code=$?

  # The first JSON line on stdout should be the version_mismatch announcement.
  local first_line
  first_line="$(head -n1 "$stdout_file")"

  local mismatch_status action existing_version pin
  mismatch_status="$(printf '%s' "$first_line" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["status"])' 2>/dev/null || echo "")"
  [ "$mismatch_status" = "version_mismatch" ] || {
    printf '  ERROR: expected status=version_mismatch on first stdout line, got: %s\n' "$first_line"
    return 1
  }

  action="$(printf '%s' "$first_line" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["action"])' 2>/dev/null || echo "")"
  [ "$action" = "installing_fresh_alongside" ] || {
    printf '  ERROR: expected action=installing_fresh_alongside, got: %s\n' "$action"
    return 1
  }

  existing_version="$(printf '%s' "$first_line" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["existing_version"])' 2>/dev/null || echo "")"
  [ "$existing_version" = "9.9.9" ] || {
    printf '  ERROR: expected existing_version=9.9.9, got: %s\n' "$existing_version"
    return 1
  }

  pin="$(printf '%s' "$first_line" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["pin"])' 2>/dev/null || echo "")"
  [ "$pin" = "4.0.5" ] || {
    printf '  ERROR: expected pin=4.0.5, got: %s\n' "$pin"
    return 1
  }

  return 0
}

# ---------------------------------------------------------------------------
# Test 2: No mismatch when versions match — no version_mismatch announcement.
# ---------------------------------------------------------------------------
test_no_mismatch_when_versions_match() {
  local cfg_dir="$SHARED_TMP/cfg_vm2"
  local state_dir="$SHARED_TMP/state_vm2"

  # Build a fake SPheno install at version 4.0.5 (matching the pin).
  local fake_root="$SHARED_TMP/SPheno-4.0.5"
  mkdir -p "$cfg_dir/hephaestus" "$state_dir" "$fake_root/bin"

  local fake_bin="$fake_root/bin/SPheno"
  printf '#!/usr/bin/env bash\necho "SPheno usage: provide LesHouches input"\n' > "$fake_bin"
  chmod +x "$fake_bin"
  touch "$fake_root/Makefile"

  python3 -c "
import json, os
cfg = '$cfg_dir/hephaestus/config.json'
os.makedirs(os.path.dirname(cfg), exist_ok=True)
with open(cfg, 'w') as f:
    json.dump({'spheno_path': '$fake_bin', 'spheno_version': '4.0.5'}, f)
"

  # Fake curl that fails immediately so install aborts after mismatch check.
  local fake_bin_dir="$SHARED_TMP/fakepath_vm2"
  mkdir -p "$fake_bin_dir"
  printf '#!/usr/bin/env bash\nexit 1\n' > "$fake_bin_dir/curl"
  chmod +x "$fake_bin_dir/curl"

  local stdout_file="$SHARED_TMP/stdout_vm2.txt"
  local exit_code=0
  PATH="$fake_bin_dir:$PATH" \
    XDG_CONFIG_HOME="$cfg_dir" \
    HEPPH_STATE_ROOT="$state_dir" \
    HEPPH_SPHENO_VERSION="4.0.5" \
    bash "$SCRIPT" install \
    >"$stdout_file" 2>/dev/null || exit_code=$?

  # No version_mismatch line should appear in stdout.
  if grep -q '"status":"version_mismatch"' "$stdout_file" 2>/dev/null; then
    printf '  ERROR: unexpected version_mismatch line found in stdout\n'
    return 1
  fi
  return 0
}

# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------
_run_test "version_mismatch: announcement emitted with correct fields" \
  test_version_mismatch_announcement
_run_test "no_mismatch: versions match → no version_mismatch announcement" \
  test_no_mismatch_when_versions_match

echo ""
printf 'Results: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
