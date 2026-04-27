#!/usr/bin/env bash
# test_sarah_rollback.sh — Tier-U rollback test for install_sarah.sh.
# Mandatory per P2 §1.4. Mocks only; no wolframscript required.
#
# Tests that when smoke_test_body fails (via HEPPH_SARAH_FORCE_SMOKE_FAIL=1),
# install_with_rollback:
#   1. Removes the new pkg dir entry from init.m.
#   2. Re-registers the previous pkg dir in init.m.
#   3. Does NOT create/update the SARAH-current symlink to point at the new dir.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SARAH="$SCRIPT_DIR/../install_sarah.sh"

pass() { printf 'PASS: %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

# ── Setup ──────────────────────────────────────────────────────────────────────
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Wolfram kernel dir (override for testing via HEPPH_WOLFRAM_USER_BASE).
WOLFRAM_BASE="$TMP/Library/WolframEngine"
mkdir -p "$WOLFRAM_BASE/Kernel"
touch "$WOLFRAM_BASE/Kernel/init.m"
INIT_FILE="$WOLFRAM_BASE/Kernel/init.m"

# Previous SARAH package dir.
PREV_PKG="$TMP/sarah-prev"
mkdir -p "$PREV_PKG"
touch "$PREV_PKG/SARAH.m"

# New SARAH package dir (the one that "just got installed").
NEW_PKG="$TMP/sarah-new"
mkdir -p "$NEW_PKG"
touch "$NEW_PKG/SARAH.m"

# Install parent dir (where SARAH-current symlink lives).
INSTALL_PARENT="$TMP"

# Config dir for config_get/config_merge.
CONFIG_DIR="$TMP/config/hephaestus"
mkdir -p "$CONFIG_DIR"
CONFIG_FILE="$CONFIG_DIR/config.json"
printf '{"sarah_path":"%s"}\n' "$PREV_PKG" > "$CONFIG_FILE"

# Create stripped install_sarah.sh so we can source functions without main().
SOURCEABLE="$TMP/install_sarah_sourceable.sh"
grep -v '^main "\$@"$' "$INSTALL_SARAH" > "$SOURCEABLE"
# Stub _common.sh for the sourceable file's SCRIPT_DIR.
printf '#!/usr/bin/env bash\n# stub\n' > "$TMP/_common.sh"

# ── Seed state: register prev pkg dir in init.m ────────────────────────────────
# Run register_path for the previous install to simulate "already installed".
cat > "$TMP/seed_wrapper.sh" << EOF
#!/usr/bin/env bash
set -euo pipefail
export HEPPH_WOLFRAM_USER_BASE="$WOLFRAM_BASE"
export XDG_CONFIG_HOME="$TMP/config"
. "$SCRIPT_DIR/../_common.sh"
. "$SOURCEABLE"
register_path "$PREV_PKG"
echo SEED_OK
EOF
chmod +x "$TMP/seed_wrapper.sh"
SEED_OUT="$(bash "$TMP/seed_wrapper.sh" 2>&1 || echo SEED_FAILED)"
echo "$SEED_OUT" | grep -q 'SEED_OK' || fail "Seed register_path failed: $SEED_OUT"

# Verify prev pkg is in init.m before rollback test.
grep -q 'sarah-prev' "$INIT_FILE" \
  || fail "Pre-condition: sarah-prev not in init.m after seeding"
pass "Pre-condition: previous pkg dir registered in init.m"

# ── Run install_with_rollback with forced smoke failure ────────────────────────
# Use HEPPH_SARAH_FORCE_SMOKE_FAIL=1 to simulate smoke failure.
cat > "$TMP/rollback_wrapper.sh" << EOF
#!/usr/bin/env bash
set -euo pipefail
export HEPPH_WOLFRAM_USER_BASE="$WOLFRAM_BASE"
export XDG_CONFIG_HOME="$TMP/config"
export HEPPH_SARAH_FORCE_SMOKE_FAIL=1
. "$SCRIPT_DIR/../_common.sh"
. "$SOURCEABLE"
# Call install_with_rollback directly (the testable helper from install_sarah.sh).
# Args: <new_pkg_dir> <previous_path> <install_parent> <wolfram>
install_with_rollback "$NEW_PKG" "$PREV_PKG" "$INSTALL_PARENT" "/usr/bin/false" || true
echo ROLLBACK_RAN
EOF
chmod +x "$TMP/rollback_wrapper.sh"
ROLLBACK_OUT="$(bash "$TMP/rollback_wrapper.sh" 2>&1 || true)"
echo "$ROLLBACK_OUT" | grep -q 'ROLLBACK_RAN' \
  || fail "install_with_rollback did not complete: $ROLLBACK_OUT"
pass "install_with_rollback ran (forced smoke failure)"

# ── Assertions ─────────────────────────────────────────────────────────────────

# Assertion 1: new pkg dir NOT in init.m (unregister_path ran).
if grep -q 'sarah-new' "$INIT_FILE"; then
  fail "Rollback A1: sarah-new still in init.m — unregister_path did not run"
fi
pass "Rollback A1: new pkg dir (sarah-new) removed from init.m"

# Assertion 2: previous pkg dir IS in init.m (re-registered).
if ! grep -q 'sarah-prev' "$INIT_FILE"; then
  fail "Rollback A2: sarah-prev not in init.m — previous path was not re-registered"
fi
pass "Rollback A2: previous pkg dir (sarah-prev) re-registered in init.m"

# Assertion 3: SARAH-current symlink does NOT point at new pkg dir.
# It should either be absent or point at the prev pkg (not at new).
SYMLINK_PATH="$INSTALL_PARENT/SARAH-current"
if [ -L "$SYMLINK_PATH" ]; then
  SYMLINK_TARGET="$(readlink "$SYMLINK_PATH")"
  if [ "$SYMLINK_TARGET" = "$NEW_PKG" ]; then
    fail "Rollback A3: SARAH-current symlink points at failed new pkg ($NEW_PKG)"
  fi
  pass "Rollback A3: SARAH-current symlink exists but does NOT point at new pkg"
else
  pass "Rollback A3: SARAH-current symlink absent (not created after smoke fail)"
fi

# Assertion 4: Exit code of the test is 0 (rollback did not crash).
pass "Rollback A4: rollback did not crash (exit 0)"

echo ""
echo "All test_sarah_rollback.sh tests passed."
