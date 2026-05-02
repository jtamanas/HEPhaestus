#!/usr/bin/env bash
# test_detect_config.sh — unit tests for _probe.sh (detect) and use-path config parsing.
# Run: bash tests/test_detect_config.sh
# Exit 0 = all tests pass (5/5).
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

# ── Test 1: detect emits "missing" when no config ─────────────────────────────
t1_detect_missing() {
  local tmpdir; tmpdir="$(make_config)"
  local status
  status=$(XDG_CONFIG_HOME="$tmpdir/cfg" \
           HEPPH_STATE_ROOT="$tmpdir/state" \
           bash "$SKILL_DIR/_probe.sh" 2>/dev/null \
           | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])")
  if [ "$status" = "missing" ]; then
    _pass "detect → missing when no config"
  else
    _fail "detect → expected 'missing', got '$status'"
  fi
  rm -rf "$tmpdir"
}

# ── Test 2: detect emits "configured" when config + binary present ────────────
t2_detect_configured() {
  local tmpdir; tmpdir="$(make_config)"
  local cfg_dir="$tmpdir/cfg/hephaestus"
  mkdir -p "$cfg_dir"
  # Create fake class binary stub
  local class_src="$tmpdir/class_src"
  mkdir -p "$class_src"
  echo '#!/bin/bash' > "$class_src/class"; chmod +x "$class_src/class"

  # Write config
  cat > "$cfg_dir/config.json" <<JSON
{
  "class_path": "$class_src",
  "class_version": "3.3.4",
  "classy_version": "3.3.4",
  "class_openmp_enabled": "1"
}
JSON

  local status
  status=$(XDG_CONFIG_HOME="$tmpdir/cfg" \
           HEPPH_STATE_ROOT="$tmpdir/state" \
           bash "$SKILL_DIR/_probe.sh" 2>/dev/null \
           | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])")
  if [ "$status" = "configured" ]; then
    _pass "detect → configured when config + binary present"
  else
    _fail "detect → expected 'configured', got '$status'"
  fi
  rm -rf "$tmpdir"
}

# ── Test 3: detect emits "missing" when config path missing on disk ───────────
t3_detect_missing_path() {
  local tmpdir; tmpdir="$(make_config)"
  local cfg_dir="$tmpdir/cfg/hephaestus"
  mkdir -p "$cfg_dir"
  cat > "$cfg_dir/config.json" <<JSON
{
  "class_path": "$tmpdir/nonexistent",
  "class_version": "3.3.4"
}
JSON
  local status
  status=$(XDG_CONFIG_HOME="$tmpdir/cfg" \
           HEPPH_STATE_ROOT="$tmpdir/state" \
           bash "$SKILL_DIR/_probe.sh" 2>/dev/null \
           | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])")
  if [ "$status" = "missing" ]; then
    _pass "detect → missing when config path absent on disk"
  else
    _fail "detect → expected 'missing' for absent path, got '$status'"
  fi
  rm -rf "$tmpdir"
}

# ── Test 4: configured JSON includes expected keys ────────────────────────────
t4_config_keys() {
  local tmpdir; tmpdir="$(make_config)"
  local cfg_dir="$tmpdir/cfg/hephaestus"
  mkdir -p "$cfg_dir"
  local class_src="$tmpdir/class_src"
  mkdir -p "$class_src"
  echo '#!/bin/bash' > "$class_src/class"; chmod +x "$class_src/class"

  cat > "$cfg_dir/config.json" <<JSON
{
  "class_path": "$class_src",
  "class_version": "3.3.4",
  "classy_version": "3.3.4",
  "class_openmp_enabled": "1"
}
JSON

  local output
  output=$(XDG_CONFIG_HOME="$tmpdir/cfg" \
           HEPPH_STATE_ROOT="$tmpdir/state" \
           bash "$SKILL_DIR/_probe.sh" 2>/dev/null)

  local class_version openmp
  class_version=$(echo "$output" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('class_version',''))")
  openmp=$(echo "$output" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('class_openmp_enabled',''))")

  if [ "$class_version" = "3.3.4" ] && [ "$openmp" = "1" ]; then
    _pass "detect → JSON includes class_version and class_openmp_enabled"
  else
    _fail "detect → class_version='$class_version' openmp='$openmp'; expected 3.3.4/1"
  fi
  rm -rf "$tmpdir"
}

# ── Test 5: use-path registers config keys ────────────────────────────────────
t5_use_path_config_write() {
  local tmpdir; tmpdir="$(make_config)"
  local cfg_dir="$tmpdir/cfg/hephaestus"
  mkdir -p "$cfg_dir"
  local class_src="$tmpdir/class_src"
  mkdir -p "$class_src"
  echo '#!/bin/bash' > "$class_src/class"; chmod +x "$class_src/class"

  local rc=0
  XDG_CONFIG_HOME="$tmpdir/cfg" \
  HEPPH_STATE_ROOT="$tmpdir/state" \
  bash "$SKILL_DIR/install.sh" use-path "$class_src" 2>/dev/null || rc=$?

  if [ $rc -eq 0 ]; then
    local class_path_written
    class_path_written=$(python3 -c "
import json
with open('$cfg_dir/config.json') as f:
    d = json.load(f)
print(d.get('class_path',''))
")
    if [ "$class_path_written" = "$class_src" ]; then
      _pass "use-path → writes class_path to config"
    else
      _fail "use-path → class_path='$class_path_written'; expected '$class_src'"
    fi
  else
    _fail "use-path → script exited $rc"
  fi
  rm -rf "$tmpdir"
}

# ── Run all tests ─────────────────────────────────────────────────────────────
t1_detect_missing
t2_detect_configured
t3_detect_missing_path
t4_config_keys
t5_use_path_config_write

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
