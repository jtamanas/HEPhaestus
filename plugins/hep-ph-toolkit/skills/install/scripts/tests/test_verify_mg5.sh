#!/usr/bin/env bash
# test_verify_mg5.sh — tier-U unit tests for install_mg5.sh verify subcommand.
# Covers WS2-T1 acceptance criteria per plan-final.md §2.2.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
MG5_SCRIPT="$INSTALL_DIR/scripts/install_mg5.sh"
PLUGIN_ROOT="$INSTALL_DIR"

pass() { printf 'PASS: %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

# Helper: make a mock mg5_aMC executable in a temp dir.
# Usage: make_mock <tmpdir> <stdout_content> <exit_code>
make_mock() {
  local dir="$1" stdout_content="$2" exit_code="${3:-0}"
  mkdir -p "$dir/bin"
  local script="$dir/bin/mg5_aMC"
  cat > "$script" <<MOCK
#!/usr/bin/env bash
printf '%s' '${stdout_content}'
exit ${exit_code}
MOCK
  chmod +x "$script"
  echo "$script"
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. no-path → not_configured, exit 17
# ─────────────────────────────────────────────────────────────────────────────
T=$(mktemp -d)
rc=0
out=$(HOME="$T" XDG_CONFIG_HOME="$T/xdg" bash "$MG5_SCRIPT" verify 2>/dev/null) || rc=$?
[ "$rc" -eq 17 ] || fail "no-path: expected exit 17, got $rc"
printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='not_configured', d" \
  || fail "no-path: status != not_configured"
pass "no-path: exit 17 and status=not_configured"
rm -rf "$T"

# ─────────────────────────────────────────────────────────────────────────────
# 2. bad-path → missing, exit 16
# ─────────────────────────────────────────────────────────────────────────────
T=$(mktemp -d)
rc=0
out=$(HOME="$T" XDG_CONFIG_HOME="$T/xdg" bash "$MG5_SCRIPT" verify --path /does/not/exist/mg5_aMC 2>/dev/null) || rc=$?
[ "$rc" -eq 16 ] || fail "bad-path: expected exit 16, got $rc"
printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='missing', d" \
  || fail "bad-path: status != missing"
printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); h=[x['code'] for x in d.get('hints',[])]; assert 'path_not_found' in h, d" \
  || fail "bad-path: hint path_not_found missing"
pass "bad-path: exit 16, status=missing, hint=path_not_found"
rm -rf "$T"

# ─────────────────────────────────────────────────────────────────────────────
# 3. happy path → ok, version=3.5.6
# Banner: "MadGraph5_aMC@NLO v3.5.6"
# ─────────────────────────────────────────────────────────────────────────────
T=$(mktemp -d)
BANNER='MadGraph5_aMC@NLO  v3.5.6\nUsage: ...\n'
mock=$(make_mock "$T" "$BANNER" 0)
rc=0
out=$(HOME="$T" XDG_CONFIG_HOME="$T/xdg" bash "$MG5_SCRIPT" verify --path "$mock" 2>/dev/null) || rc=$?
[ "$rc" -eq 0 ] || fail "happy: expected exit 0, got $rc"
printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='ok', d; assert d['version']=='3.5.6', d" \
  || fail "happy: status != ok or version != 3.5.6"
pass "happy: exit 0, status=ok, version=3.5.6"
rm -rf "$T"

# ─────────────────────────────────────────────────────────────────────────────
# 4. stale banner (no MadGraph5_aMC@NLO string) → installed_broken, hint mg5_version_probe_stale
# ─────────────────────────────────────────────────────────────────────────────
T=$(mktemp -d)
BANNER='Usage: mg5_aMC [options]\n'
mock=$(make_mock "$T" "$BANNER" 0)
rc=0
out=$(HOME="$T" XDG_CONFIG_HOME="$T/xdg" bash "$MG5_SCRIPT" verify --path "$mock" 2>/dev/null) || rc=$?
[ "$rc" -eq 15 ] || fail "stale-banner: expected exit 15, got $rc"
printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='installed_broken', d; h=[x['code'] for x in d.get('hints',[])]; assert 'mg5_version_probe_stale' in h, d" \
  || fail "stale-banner: status or hint wrong"
pass "stale-banner: exit 15, installed_broken, hint=mg5_version_probe_stale"
rm -rf "$T"

# ─────────────────────────────────────────────────────────────────────────────
# 5. --help exits non-zero → installed_broken
# ─────────────────────────────────────────────────────────────────────────────
T=$(mktemp -d)
BANNER='MadGraph5_aMC@NLO  v3.5.6\n'
mock=$(make_mock "$T" "$BANNER" 1)
rc=0
out=$(HOME="$T" XDG_CONFIG_HOME="$T/xdg" bash "$MG5_SCRIPT" verify --path "$mock" 2>/dev/null) || rc=$?
[ "$rc" -eq 15 ] || fail "--help-nonzero: expected exit 15, got $rc"
printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='installed_broken', d" \
  || fail "--help-nonzero: status != installed_broken"
pass "--help exits 1: exit 15, installed_broken"
rm -rf "$T"

# ─────────────────────────────────────────────────────────────────────────────
# 6. tier-2 enrichment agreement:
#    mock at $tmp/bin/mg5_aMC, VERSION=3.5.6, banner=3.5.6 → ok, version=3.5.6
# ─────────────────────────────────────────────────────────────────────────────
T=$(mktemp -d)
BANNER='MadGraph5_aMC@NLO  v3.5.6\n'
mock=$(make_mock "$T" "$BANNER" 0)
echo "3.5.6" > "$T/VERSION"
rc=0
out=$(HOME="$T" XDG_CONFIG_HOME="$T/xdg" bash "$MG5_SCRIPT" verify --path "$mock" 2>/dev/null) || rc=$?
[ "$rc" -eq 0 ] || fail "tier2-agree: expected exit 0, got $rc"
printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='ok', d; assert d['version']=='3.5.6', d" \
  || fail "tier2-agree: wrong status or version"
pass "tier2-agree: exit 0, ok, version=3.5.6"
rm -rf "$T"

# ─────────────────────────────────────────────────────────────────────────────
# 7. tier-2 disagreement: banner=3.5.6, VERSION=3.5.7 → ok, version=3.5.6, detail has both
# ─────────────────────────────────────────────────────────────────────────────
T=$(mktemp -d)
BANNER='MadGraph5_aMC@NLO  v3.5.6\n'
mock=$(make_mock "$T" "$BANNER" 0)
echo "3.5.7" > "$T/VERSION"
rc=0
out=$(HOME="$T" XDG_CONFIG_HOME="$T/xdg" bash "$MG5_SCRIPT" verify --path "$mock" 2>/dev/null) || rc=$?
[ "$rc" -eq 0 ] || fail "tier2-disagree: expected exit 0, got $rc"
printf '%s' "$out" | python3 -c "
import json,sys
d=json.load(sys.stdin)
assert d['status']=='ok', d
assert d['version']=='3.5.6', d
assert '3.5.6' in d['detail'], d
assert '3.5.7' in d['detail'], d
" || fail "tier2-disagree: status/version/detail wrong"
pass "tier2-disagree: exit 0, ok, version=3.5.6, detail contains both versions"
rm -rf "$T"

# ─────────────────────────────────────────────────────────────────────────────
# 8. tier-1 empty, tier-2 has VERSION: installed_broken (tier-2 is enrichment only)
#    Banner has no MadGraph5_aMC@NLO string; VERSION file has 3.5.6.
# ─────────────────────────────────────────────────────────────────────────────
T=$(mktemp -d)
BANNER='Usage: mg5_aMC [options]\n'
mock=$(make_mock "$T" "$BANNER" 0)
echo "3.5.6" > "$T/VERSION"
rc=0
out=$(HOME="$T" XDG_CONFIG_HOME="$T/xdg" bash "$MG5_SCRIPT" verify --path "$mock" 2>/dev/null) || rc=$?
[ "$rc" -eq 15 ] || fail "tier1-empty-tier2-only: expected exit 15, got $rc"
printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='installed_broken', d; h=[x['code'] for x in d.get('hints',[])]; assert 'mg5_version_probe_stale' in h, d" \
  || fail "tier1-empty-tier2-only: wrong status or hint"
pass "tier1-empty-tier2-only: installed_broken (tier-2 is enrichment only, not substitute)"
rm -rf "$T"

# ─────────────────────────────────────────────────────────────────────────────
# 9. timeout: mock sleeps 30s, --timeout 2 → timeout, exit 15
# ─────────────────────────────────────────────────────────────────────────────
T=$(mktemp -d)
mkdir -p "$T/bin"
cat > "$T/bin/mg5_aMC" <<'MOCK'
#!/usr/bin/env bash
sleep 30
MOCK
chmod +x "$T/bin/mg5_aMC"
rc=0
out=$(HOME="$T" XDG_CONFIG_HOME="$T/xdg" bash "$MG5_SCRIPT" verify --path "$T/bin/mg5_aMC" --timeout 2 2>/dev/null) || rc=$?
[ "$rc" -eq 15 ] || fail "timeout: expected exit 15, got $rc"
printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='timeout', d" \
  || fail "timeout: status != timeout"
pass "timeout: exit 15, status=timeout"
rm -rf "$T"

# ─────────────────────────────────────────────────────────────────────────────
# Anti-assertion: no --version in non-comment lines of install_mg5.sh (B6 enforcement)
# ─────────────────────────────────────────────────────────────────────────────
bad=$(grep -n -- '--version' "$PLUGIN_ROOT/scripts/install_mg5.sh" | grep -vE '^[0-9]+:[[:space:]]*#' || true)
[ -z "$bad" ] || fail "install_mg5.sh still references --version at non-comment line(s): $bad"
pass "B6 anti-assertion: no --version in non-comment lines of install_mg5.sh"

# ─────────────────────────────────────────────────────────────────────────────
# Syntax check
# ─────────────────────────────────────────────────────────────────────────────
bash -n "$PLUGIN_ROOT/scripts/install_mg5.sh" || fail "bash -n install_mg5.sh failed"
pass "bash -n install_mg5.sh: exit 0"

echo ""
echo "All test_verify_mg5.sh tests passed."
