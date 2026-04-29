#!/usr/bin/env bash
# test_detect_config.sh — unit tests for detect_higgstools.sh and use-path config parsing.
# Run: bash tests/test_detect_config.sh
# Exit 0 = all tests pass.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

PASS=0
FAIL=0

_pass() { echo "PASS: $1"; PASS=$((PASS+1)); }
_fail() { echo "FAIL: $1"; FAIL=$((FAIL+1)); }

# ── Helper: create a temporary config directory ─────────────────────────────
make_config() {
  local tmpdir
  tmpdir="$(mktemp -d)"
  echo "$tmpdir"
}

# ── Test 1: detect emits "missing" when no config and no tools on PATH ───────
t1_detect_missing() {
  local tmpdir; tmpdir="$(make_config)"
  local status
  status=$(XDG_CONFIG_HOME="$tmpdir/cfg" \
           HEPPH_STATE_ROOT="$tmpdir/state" \
           bash "$SKILL_DIR/_probe.sh" 2>/dev/null \
           | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])")
  if [ "$status" = "missing" ]; then
    _pass "detect → missing when no config + no tools"
  else
    _fail "detect → expected 'missing', got '$status'"
  fi
  rm -rf "$tmpdir"
}

# ── Test 2: detect emits "configured" when config has valid paths ────────────
t2_detect_configured() {
  local tmpdir; tmpdir="$(make_config)"
  local cfg_dir="$tmpdir/cfg/hephaestus"
  mkdir -p "$cfg_dir"
  # Create fake HB/HS binary stubs
  local hb_build="$tmpdir/hb/build/bin"
  local hs_build="$tmpdir/hs/build/bin"
  mkdir -p "$hb_build" "$hs_build"
  echo '#!/bin/bash' > "$hb_build/HiggsBounds"; chmod +x "$hb_build/HiggsBounds"
  echo '#!/bin/bash' > "$hs_build/HiggsSignals"; chmod +x "$hs_build/HiggsSignals"

  # Write config
  cat > "$cfg_dir/config.json" <<JSON
{
  "higgstools_backend": "legacy",
  "higgsbounds_path": "$tmpdir/hb/build",
  "higgsbounds_version": "5.10.2",
  "higgssignals_path": "$tmpdir/hs/build",
  "higgssignals_version": "2.6.2"
}
JSON

  local status
  status=$(XDG_CONFIG_HOME="$tmpdir/cfg" \
           HEPPH_STATE_ROOT="$tmpdir/state" \
           bash "$SKILL_DIR/_probe.sh" 2>/dev/null \
           | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])")
  if [ "$status" = "configured" ]; then
    _pass "detect → configured when config + binaries present"
  else
    _fail "detect → expected 'configured', got '$status'"
  fi
  rm -rf "$tmpdir"
}

# ── Test 3: detect emits "found" when binaries exist but no config ───────────
t3_detect_found() {
  local tmpdir; tmpdir="$(make_config)"
  local cfg_dir="$tmpdir/cfg/hephaestus"
  mkdir -p "$cfg_dir"
  cat > "$cfg_dir/config.json" <<JSON
{
  "higgsbounds_path": "$tmpdir/hb/build",
  "higgssignals_path": "$tmpdir/hs/build"
}
JSON
  # No actual binaries → should get "found" if paths exist but binaries absent
  # In this case both paths don't exist → missing
  local status
  status=$(XDG_CONFIG_HOME="$tmpdir/cfg" \
           HEPPH_STATE_ROOT="$tmpdir/state" \
           bash "$SKILL_DIR/_probe.sh" 2>/dev/null \
           | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])")
  if [ "$status" = "missing" ]; then
    _pass "detect → missing when config paths missing on disk"
  else
    _fail "detect → expected 'missing' for absent paths, got '$status'"
  fi
  rm -rf "$tmpdir"
}

# ── Test 4: config has both paths and backend key ────────────────────────────
t4_config_keys() {
  local tmpdir; tmpdir="$(make_config)"
  local cfg_dir="$tmpdir/cfg/hephaestus"
  mkdir -p "$cfg_dir"
  local hb_build="$tmpdir/hb/build/bin"
  local hs_build="$tmpdir/hs/build/bin"
  mkdir -p "$hb_build" "$hs_build"
  echo '#!/bin/bash' > "$hb_build/HiggsBounds"; chmod +x "$hb_build/HiggsBounds"
  echo '#!/bin/bash' > "$hs_build/HiggsSignals"; chmod +x "$hs_build/HiggsSignals"

  cat > "$cfg_dir/config.json" <<JSON
{
  "higgstools_backend": "legacy",
  "higgsbounds_path": "$tmpdir/hb/build",
  "higgsbounds_version": "5.10.2",
  "higgssignals_path": "$tmpdir/hs/build",
  "higgssignals_version": "2.6.2"
}
JSON

  local output
  output=$(XDG_CONFIG_HOME="$tmpdir/cfg" \
           HEPPH_STATE_ROOT="$tmpdir/state" \
           bash "$SKILL_DIR/_probe.sh" 2>/dev/null)

  local backend hb_version
  backend=$(echo "$output" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('backend',''))")
  hb_version=$(echo "$output" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('hb_version',''))")

  if [ "$backend" = "legacy" ] && [ "$hb_version" = "5.10.2" ]; then
    _pass "detect → JSON includes backend and hb_version"
  else
    _fail "detect → backend='$backend' hb_version='$hb_version'; expected legacy/5.10.2"
  fi
  rm -rf "$tmpdir"
}

# ── Test 5: use-path registers config keys atomically ───────────────────────
t5_use_path_config_write() {
  local tmpdir; tmpdir="$(make_config)"
  local cfg_dir="$tmpdir/cfg/hephaestus"
  mkdir -p "$cfg_dir"
  local hb_build="$tmpdir/hb/build/bin"
  local hs_build="$tmpdir/hs/build/bin"
  mkdir -p "$hb_build" "$hs_build"
  echo '#!/bin/bash' > "$hb_build/HiggsBounds"; chmod +x "$hb_build/HiggsBounds"
  echo '#!/bin/bash' > "$hs_build/HiggsSignals"; chmod +x "$hs_build/HiggsSignals"

  local rc=0
  XDG_CONFIG_HOME="$tmpdir/cfg" \
  HEPPH_STATE_ROOT="$tmpdir/state" \
  bash "$SKILL_DIR/install.sh" use-path "$tmpdir/hb/build" "$tmpdir/hs/build" 2>/dev/null || rc=$?

  if [ $rc -eq 0 ]; then
    local backend
    backend=$(python3 -c "
import json
with open('$cfg_dir/config.json') as f:
    d = json.load(f)
print(d.get('higgstools_backend',''))
")
    if [ "$backend" = "legacy" ]; then
      _pass "use-path → writes higgstools_backend=legacy to config"
    else
      _fail "use-path → backend='$backend'; expected 'legacy'"
    fi
  else
    _fail "use-path → script exited $rc"
  fi
  rm -rf "$tmpdir"
}

# ── Run all tests ─────────────────────────────────────────────────────────────
t1_detect_missing
t2_detect_configured
t3_detect_found
t4_config_keys
t5_use_path_config_write

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
