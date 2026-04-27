#!/usr/bin/env bash
# test_verify_spheno.sh — tier-U unit tests for install_spheno.sh cmd_verify
# and compile() ifort-fallback behavior.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass() { printf 'PASS: %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

# ── Helpers ──────────────────────────────────────────────────────────────────

# make_mock_spheno <dir> <exit_code> <stdout_content>
# Creates an executable mock SPheno binary at <dir>/bin/SPheno.
make_mock_spheno() {
  local dir="$1" exit_code="$2" stdout_content="$3"
  mkdir -p "$dir/bin"
  cat > "$dir/bin/SPheno" <<MOCKEOF
#!/usr/bin/env bash
printf '%s' '$stdout_content'
exit $exit_code
MOCKEOF
  chmod +x "$dir/bin/SPheno"
}

run_verify() {
  # run_verify [extra args...] → sets $verify_rc and $verify_out
  verify_out=""
  verify_rc=0
  verify_out=$(HOME="$(mktemp -d)" XDG_CONFIG_HOME="$(mktemp -d)" \
    bash "$INSTALL_DIR/scripts/install_spheno.sh" verify "$@" 2>/dev/null) || verify_rc=$?
}

# ── Test 1: happy path — banner with version ─────────────────────────────────
T1=$(mktemp -d)
make_mock_spheno "$T1" 1 "SPheno v4.0.5\nusage: SPheno <input file>\n"
run_verify --path "$T1/bin/SPheno"
[ "$verify_rc" -eq 0 ] || fail "T1: expected exit 0, got $verify_rc"
printf '%s' "$verify_out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['ok']==True, d; assert d['status']=='ok', d; assert d['version']=='4.0.5', d" \
  || fail "T1: JSON check failed: $verify_out"
pass "T1: happy path (banner + version 4.0.5) → ok, version 4.0.5"
rm -rf "$T1"

# ── Test 2: happy path — banner without version ──────────────────────────────
T2=$(mktemp -d)
make_mock_spheno "$T2" 1 "usage: SPheno input file\n"
run_verify --path "$T2/bin/SPheno"
[ "$verify_rc" -eq 0 ] || fail "T2: expected exit 0, got $verify_rc"
printf '%s' "$verify_out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['ok']==True, d; assert d['status']=='ok', d" \
  || fail "T2: JSON check failed: $verify_out"
pass "T2: happy path (banner, no version) → ok"
rm -rf "$T2"

# ── Test 3: dylib failure ─────────────────────────────────────────────────────
T3=$(mktemp -d)
make_mock_spheno "$T3" 1 "dyld: Library not loaded: @rpath/libifcore.dylib\nReferenced from: $T3/bin/SPheno\nReason: image not found\n"
run_verify --path "$T3/bin/SPheno"
[ "$verify_rc" -ne 0 ] || fail "T3: expected non-zero exit, got 0"
printf '%s' "$verify_out" | python3 -c "
import json,sys
d=json.load(sys.stdin)
assert d['ok']==False, d
assert d['status']=='installed_broken', d
assert any(h['code']=='shared_library_missing' for h in d.get('hints',[])), d
" || fail "T3: JSON check failed: $verify_out"
pass "T3: dylib failure → installed_broken, hint shared_library_missing"
rm -rf "$T3"

# ── Test 4: garbage output ────────────────────────────────────────────────────
T4=$(mktemp -d)
make_mock_spheno "$T4" 1 "some error occurred\n"
run_verify --path "$T4/bin/SPheno"
[ "$verify_rc" -ne 0 ] || fail "T4: expected non-zero exit, got 0"
printf '%s' "$verify_out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['ok']==False, d; assert d['status']=='installed_broken', d" \
  || fail "T4: JSON check failed: $verify_out"
pass "T4: garbage output → installed_broken (no specific hint)"
rm -rf "$T4"

# ── Test 5: timeout ───────────────────────────────────────────────────────────
T5=$(mktemp -d)
mkdir -p "$T5/bin"
cat > "$T5/bin/SPheno" <<'MOCKEOF'
#!/usr/bin/env bash
sleep 30
MOCKEOF
chmod +x "$T5/bin/SPheno"
run_verify --path "$T5/bin/SPheno" --timeout 2
[ "$verify_rc" -ne 0 ] || fail "T5: expected non-zero exit (timeout), got 0"
printf '%s' "$verify_out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['ok']==False, d; assert d['status']=='timeout', d" \
  || fail "T5: JSON check failed: $verify_out"
pass "T5: timeout → status=timeout, exit non-zero"
rm -rf "$T5"

# ── Test 6: missing path ──────────────────────────────────────────────────────
run_verify --path /does/not/exist/SPheno
[ "$verify_rc" -eq 16 ] || fail "T6: expected exit 16, got $verify_rc"
printf '%s' "$verify_out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='missing', d; assert any(h['code']=='path_not_found' for h in d.get('hints',[])), d" \
  || fail "T6: JSON check failed: $verify_out"
pass "T6: missing path → missing, hint path_not_found, exit 16"

# ── Test 7: no path + empty config → not_configured ──────────────────────────
verify_rc=0
verify_out=$(HOME="$(mktemp -d)" XDG_CONFIG_HOME="$(mktemp -d)" \
  bash "$INSTALL_DIR/scripts/install_spheno.sh" verify 2>/dev/null) || verify_rc=$?
[ "$verify_rc" -eq 17 ] || fail "T7: expected exit 17 (not_configured), got $verify_rc"
printf '%s' "$verify_out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='not_configured', d" \
  || fail "T7: JSON check failed: $verify_out"
pass "T7: no path + empty config → not_configured, exit 17"

# ── Test 8: stdout is exactly one JSON line ───────────────────────────────────
T8=$(mktemp -d)
make_mock_spheno "$T8" 1 "SPheno v4.0.5\nusage: SPheno <input file>\n"
stdout_lines=$(HOME="$(mktemp -d)" XDG_CONFIG_HOME="$(mktemp -d)" \
  bash "$INSTALL_DIR/scripts/install_spheno.sh" verify --path "$T8/bin/SPheno" 2>/dev/null | wc -l | tr -d ' ')
[ "$stdout_lines" -eq 1 ] || fail "T8: expected 1 stdout line, got $stdout_lines"
pass "T8: stdout is exactly one JSON line"
rm -rf "$T8"

# ── Test 9: no 'probe' field in JSON output ───────────────────────────────────
T9=$(mktemp -d)
make_mock_spheno "$T9" 1 "SPheno v4.0.5\nusage: SPheno <input file>\n"
probe_present=$(HOME="$(mktemp -d)" XDG_CONFIG_HOME="$(mktemp -d)" \
  bash "$INSTALL_DIR/scripts/install_spheno.sh" verify --path "$T9/bin/SPheno" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('yes' if 'probe' in d else 'no')")
[ "$probe_present" = "no" ] || fail "T9: 'probe' key must not appear in JSON output"
pass "T9: 'probe' key absent from JSON output"
rm -rf "$T9"

# ── Test 10: ifort fallback — broken ifort on PATH uses gfortran ──────────────
test_ifort_fallback() {
  local tmp_mock
  tmp_mock="$(mktemp -d)"
  local make_log="/tmp/make_args_$$.log"
  rm -f "$make_log"

  # Mock ifort: exits non-zero on --version (simulating broken Intel shim).
  cat > "$tmp_mock/ifort" <<'MOCKEOF'
#!/usr/bin/env bash
exit 1
MOCKEOF
  chmod +x "$tmp_mock/ifort"

  # Mock make: logs its args to make_log and exits 0.
  cat > "$tmp_mock/make" <<MOCKEOF
#!/usr/bin/env bash
printf '%s\n' "\$@" >> "$make_log"
exit 0
MOCKEOF
  chmod +x "$tmp_mock/make"

  # Also need a mock source dir with a minimal Makefile placeholder.
  local src_dir
  src_dir="$(mktemp -d)"
  touch "$src_dir/Makefile"

  # Build a driver script that sources install_spheno.sh functions and
  # calls compile() directly. We source the real _common.sh first, then
  # eval the spheno functions (stripping the header lines that would reset
  # SCRIPT_DIR and re-source _common.sh, which would fail in /tmp).
  local driver
  driver="$(mktemp)"
  cat > "$driver" <<DRIVEREOF
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$INSTALL_DIR/scripts"
. "\$SCRIPT_DIR/_common.sh"
# Load spheno functions: strip shebang, set -e, SCRIPT_DIR assignment,
# _common.sh sourcing, and the final main call — these are already handled.
_spheno_src="\$(
  grep -v '^#!/' '$INSTALL_DIR/scripts/install_spheno.sh' |
  grep -v '^set -euo pipefail' |
  grep -v '^_LOG_TAG=' |
  grep -v 'SCRIPT_DIR=' |
  grep -v '\. "\$SCRIPT_DIR/_common.sh"' |
  grep -v '^# shellcheck' |
  grep -v '^main \"\\\$@\"\$'
)"
eval "\$_spheno_src"
compile "$src_dir"
DRIVEREOF
  chmod +x "$driver"

  PATH="$tmp_mock:$PATH" bash "$driver" 2>/dev/null || true
  rm -f "$driver"

  # Assert make was called with F90=gfortran.
  if [ -f "$make_log" ]; then
    if grep -q 'F90=gfortran' "$make_log"; then
      pass "T10: broken ifort → compile() passes F90=gfortran to make"
    else
      fail "T10: make_args.log does not contain F90=gfortran. Contents: $(cat "$make_log")"
    fi
  else
    fail "T10: make_args.log not created — make mock may not have been called"
  fi

  rm -rf "$tmp_mock" "$src_dir"
  rm -f "$make_log"
}
test_ifort_fallback

# ── Test 11: HEPPH_F90_COMPILER env override ──────────────────────────────────
test_env_override() {
  local tmp_mock
  tmp_mock="$(mktemp -d)"
  local make_log="/tmp/make_args_env_$$.log"
  rm -f "$make_log"

  # Mock ifort: exits non-zero (doesn't matter; env override wins).
  cat > "$tmp_mock/ifort" <<'MOCKEOF'
#!/usr/bin/env bash
exit 1
MOCKEOF
  chmod +x "$tmp_mock/ifort"

  # Mock make: logs its args and exits 0.
  cat > "$tmp_mock/make" <<MOCKEOF
#!/usr/bin/env bash
printf '%s\n' "\$@" >> "$make_log"
exit 0
MOCKEOF
  chmod +x "$tmp_mock/make"

  local src_dir
  src_dir="$(mktemp -d)"
  touch "$src_dir/Makefile"

  # Same driver-script trick as T10, with HEPPH_F90_COMPILER set.
  local driver
  driver="$(mktemp)"
  cat > "$driver" <<DRIVEREOF
#!/usr/bin/env bash
set -euo pipefail
export HEPPH_F90_COMPILER=gfortran-13
SCRIPT_DIR="$INSTALL_DIR/scripts"
. "\$SCRIPT_DIR/_common.sh"
_spheno_src="\$(
  grep -v '^#!/' '$INSTALL_DIR/scripts/install_spheno.sh' |
  grep -v '^set -euo pipefail' |
  grep -v '^_LOG_TAG=' |
  grep -v 'SCRIPT_DIR=' |
  grep -v '\. "\$SCRIPT_DIR/_common.sh"' |
  grep -v '^# shellcheck' |
  grep -v '^main \"\\\$@\"\$'
)"
eval "\$_spheno_src"
compile "$src_dir"
DRIVEREOF
  chmod +x "$driver"

  PATH="$tmp_mock:$PATH" bash "$driver" 2>/dev/null || true
  rm -f "$driver"

  if [ -f "$make_log" ]; then
    if grep -q 'F90=gfortran-13' "$make_log"; then
      pass "T11: HEPPH_F90_COMPILER=gfortran-13 → compile() passes F90=gfortran-13 to make"
    else
      fail "T11: make_args.log does not contain F90=gfortran-13. Contents: $(cat "$make_log")"
    fi
  else
    fail "T11: make_args.log not created — make mock may not have been called"
  fi

  rm -rf "$tmp_mock" "$src_dir"
  rm -f "$make_log"
}
test_env_override

# ── Test 12: bash -n syntax check ────────────────────────────────────────────
bash -n "$INSTALL_DIR/scripts/install_spheno.sh" \
  || fail "T12: bash -n install_spheno.sh failed"
pass "T12: bash -n syntax check passes"

echo ""
echo "All test_verify_spheno.sh tests passed."
