#!/usr/bin/env bash
# test_verify_sarah.sh — Tier-U tests for install_sarah.sh cmd_verify.
# No network, no real wolframscript required. All scenarios use mock scripts.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SARAH="$SCRIPT_DIR/../install_sarah.sh"

pass() { printf 'PASS: %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

# ── Setup: tmp dirs ────────────────────────────────────────────────────────────
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

SARAH_DIR="$TMP/sarah-pkg"
mkdir -p "$SARAH_DIR"
touch "$SARAH_DIR/SARAH.m"

BIN_DIR="$TMP/bin"
mkdir -p "$BIN_DIR"

# ── Test 1: happy path ─────────────────────────────────────────────────────────
cat > "$BIN_DIR/wolframscript_happy" << 'MOCK'
#!/usr/bin/env bash
printf 'SARAH 4.15.3 loaded\nVERSION:4.15.3\n'
exit 0
MOCK
chmod +x "$BIN_DIR/wolframscript_happy"

rc=0
out="$("$INSTALL_SARAH" verify \
    --path "$SARAH_DIR" \
    --wolfram-path "$BIN_DIR/wolframscript_happy")" || rc=$?
[ "$rc" = "0" ]                         || fail "happy: expected exit 0, got $rc. out=$out"
echo "$out" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok'" \
  || fail "happy: expected status ok, got: $out"
echo "$out" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['version']=='4.15.3'" \
  || fail "happy: expected version 4.15.3, got: $out"
echo "$out" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['tool']=='sarah'" \
  || fail "happy: expected tool sarah, got: $out"
echo "$out" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['ok']==True" \
  || fail "happy: expected ok=True, got: $out"
pass "happy path: ok, version 4.15.3"

# ── Test 2: no VERSION line → installed_broken + hint kernel_init_m_path ───────
cat > "$BIN_DIR/wolframscript_noversion" << 'MOCK'
#!/usr/bin/env bash
printf 'SARAH banner only\nNo version here\n'
exit 0
MOCK
chmod +x "$BIN_DIR/wolframscript_noversion"

rc=0
out="$("$INSTALL_SARAH" verify \
    --path "$SARAH_DIR" \
    --wolfram-path "$BIN_DIR/wolframscript_noversion")" || rc=$?
[ "$rc" = "15" ] || fail "no-version: expected exit 15, got $rc"
echo "$out" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='installed_broken'" \
  || fail "no-version: expected installed_broken, got: $out"
echo "$out" | python3 -c "import sys,json; d=json.load(sys.stdin); codes=[h['code'] for h in d.get('hints',[])]; assert 'kernel_init_m_path' in codes" \
  || fail "no-version: expected hint kernel_init_m_path, got: $out"
pass "no VERSION line → installed_broken + hint kernel_init_m_path"

# ── Test 3: exit 1 with stderr mentioning SARAH.m → installed_broken + hint ────
cat > "$BIN_DIR/wolframscript_err" << 'MOCK'
#!/usr/bin/env bash
printf 'Cannot find SARAH.m in $Path\n' >&2
exit 1
MOCK
chmod +x "$BIN_DIR/wolframscript_err"

rc=0
out="$("$INSTALL_SARAH" verify \
    --path "$SARAH_DIR" \
    --wolfram-path "$BIN_DIR/wolframscript_err")" || rc=$?
[ "$rc" = "15" ] || fail "err-stderr: expected exit 15, got $rc"
echo "$out" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='installed_broken'" \
  || fail "err-stderr: expected installed_broken, got: $out"
echo "$out" | python3 -c "import sys,json; d=json.load(sys.stdin); codes=[h['code'] for h in d.get('hints',[])]; assert 'kernel_init_m_path' in codes" \
  || fail "err-stderr: expected hint kernel_init_m_path, got: $out"
pass "exit 1 with SARAH.m in stderr → installed_broken + hint kernel_init_m_path"

# ── Test 4: timeout → timeout + exit 15 ───────────────────────────────────────
cat > "$BIN_DIR/wolframscript_slow" << 'MOCK'
#!/usr/bin/env bash
sleep 60
MOCK
chmod +x "$BIN_DIR/wolframscript_slow"

rc=0
out="$("$INSTALL_SARAH" verify \
    --path "$SARAH_DIR" \
    --wolfram-path "$BIN_DIR/wolframscript_slow" \
    --timeout 2)" || rc=$?
[ "$rc" = "15" ] || fail "timeout: expected exit 15, got $rc"
echo "$out" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='timeout'" \
  || fail "timeout: expected status timeout, got: $out"
pass "timeout (2s) → status:timeout + exit 15"

# ── Test 5: missing SARAH.m → missing + exit 16 ───────────────────────────────
EMPTY_DIR="$TMP/empty-pkg"
mkdir -p "$EMPTY_DIR"

rc=0
out="$("$INSTALL_SARAH" verify \
    --path "$EMPTY_DIR" \
    --wolfram-path "$BIN_DIR/wolframscript_happy")" || rc=$?
[ "$rc" = "16" ] || fail "missing-sarah: expected exit 16, got $rc"
echo "$out" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='missing'" \
  || fail "missing-sarah: expected status missing, got: $out"
pass "missing SARAH.m → status:missing + exit 16"

# ── Test 6: no wolframscript resolvable → installed_broken + wolfram_engine_missing
EMPTY_BIN="$TMP/empty-bin"
mkdir -p "$EMPTY_BIN"
FAKE_HOME="$TMP/fakehome"
mkdir -p "$FAKE_HOME"

rc=0
out="$(HEPPH_WOLFRAM_USER_BASE="$TMP/wolfram-base-empty" \
    XDG_CONFIG_HOME="$TMP/config-empty" \
    HOME="$FAKE_HOME" \
    PATH="$EMPTY_BIN:/usr/bin:/bin" \
    "$INSTALL_SARAH" verify --path "$SARAH_DIR")" || rc=$?
[ "$rc" = "15" ] || fail "no-wolfram: expected exit 15, got $rc"
echo "$out" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='installed_broken'" \
  || fail "no-wolfram: expected installed_broken, got: $out"
echo "$out" | python3 -c "import sys,json; d=json.load(sys.stdin); codes=[h['code'] for h in d.get('hints',[])]; assert 'wolfram_engine_missing' in codes" \
  || fail "no-wolfram: expected hint wolfram_engine_missing, got: $out"
pass "no wolframscript → installed_broken + hint wolfram_engine_missing"

# ── Anti-assertion: no AppendTo[$Path on command line in install_sarah.sh ──────
count="$(grep -c 'AppendTo\[\$Path' "$INSTALL_SARAH" || true)"
[ "$count" = "0" ] || fail "anti-assertion: AppendTo[\$Path found in install_sarah.sh (count=$count)"
pass "anti-assertion: no AppendTo[\$Path in install_sarah.sh"

# ── B4 regression: register_path twice with different dirs ────────────────────
WOLFRAM_BASE_B4="$TMP/wolfram-b4"
mkdir -p "$WOLFRAM_BASE_B4/Kernel"
touch "$WOLFRAM_BASE_B4/Kernel/init.m"
PKG_DIR_A="$TMP/sarah-a"
PKG_DIR_B="$TMP/sarah-b"
mkdir -p "$PKG_DIR_A" "$PKG_DIR_B"
touch "$PKG_DIR_A/SARAH.m" "$PKG_DIR_B/SARAH.m"

# Create a sourcing wrapper script that overrides main() before sourcing install_sarah.sh.
# Bash 3.2 (macOS default) does not support `source <(...)` process substitution.
# We use a temp wrapper script to achieve the same effect portably.
# Create stripped install_sarah.sh (without the final 'main "$@"' call)
# so we can source it and call individual functions without triggering main().
# We strip the final 'main "$@"' invocation line.
grep -v '^main "\$@"$' "$INSTALL_SARAH" > "$TMP/install_sarah_sourceable.sh"
# Create a stub _common.sh in the same dir so the sourceable script's
# SCRIPT_DIR-based '. "$SCRIPT_DIR/_common.sh"' resolve without error
# (we already sourced the real _common.sh in the wrapper).
printf '#!/usr/bin/env bash\n# stub: already sourced by wrapper\n' > "$TMP/_common.sh"

cat > "$TMP/b4_wrapper.sh" << HEREDOC
#!/usr/bin/env bash
set -euo pipefail
export HEPPH_WOLFRAM_USER_BASE="$WOLFRAM_BASE_B4"
PARENT_SCRIPT_DIR="$SCRIPT_DIR/.."
. "\$PARENT_SCRIPT_DIR/_common.sh"
. "$TMP/install_sarah_sourceable.sh"
register_path "$PKG_DIR_A"
register_path "$PKG_DIR_B"
echo B4_DOUBLE_OK
HEREDOC
chmod +x "$TMP/b4_wrapper.sh"

B4_RESULT="$(bash "$TMP/b4_wrapper.sh" 2>&1 || echo B4_FAILED)"

echo "$B4_RESULT" | grep -q 'B4_DOUBLE_OK' \
  || fail "B4 regression: register_path twice failed: $B4_RESULT"
pass "B4 regression: register_path twice with different dirs succeeds (no regex crash)"

# ── unregister_path idempotence ────────────────────────────────────────────────
WOLFRAM_BASE_UNREG="$TMP/wolfram-unreg"
mkdir -p "$WOLFRAM_BASE_UNREG/Kernel"
touch "$WOLFRAM_BASE_UNREG/Kernel/init.m"
PKG_DIR_C="$TMP/sarah-c"
mkdir -p "$PKG_DIR_C"
touch "$PKG_DIR_C/SARAH.m"

cat > "$TMP/unreg_wrapper.sh" << HEREDOC
#!/usr/bin/env bash
set -euo pipefail
export HEPPH_WOLFRAM_USER_BASE="$WOLFRAM_BASE_UNREG"
PARENT_SCRIPT_DIR="$SCRIPT_DIR/.."
. "\$PARENT_SCRIPT_DIR/_common.sh"
. "$TMP/install_sarah_sourceable.sh"
register_path "$PKG_DIR_C"
grep -q 'sarah-c' "$WOLFRAM_BASE_UNREG/Kernel/init.m" || { echo UNREG_SETUP_FAILED; exit 1; }
unregister_path "$PKG_DIR_C"
grep -q 'sarah-c' "$WOLFRAM_BASE_UNREG/Kernel/init.m" && { echo UNREG_FIRST_FAILED; exit 1; } || true
unregister_path "$PKG_DIR_C"
grep -q 'sarah-c' "$WOLFRAM_BASE_UNREG/Kernel/init.m" && { echo UNREG_SECOND_FAILED; exit 1; } || true
echo UNREG_OK
HEREDOC
chmod +x "$TMP/unreg_wrapper.sh"

UNREG_RESULT="$(bash "$TMP/unreg_wrapper.sh" 2>&1 || echo UNREG_FAILED)"

echo "$UNREG_RESULT" | grep -q 'UNREG_OK' \
  || fail "unregister_path idempotence failed: $UNREG_RESULT"
pass "unregister_path idempotence: absent after first call, no-op on second"

# ── bash -n syntax check ───────────────────────────────────────────────────────
bash -n "$INSTALL_SARAH" || fail "bash -n syntax check failed"
pass "bash -n syntax check"

echo ""
echo "All test_verify_sarah.sh tests passed."
