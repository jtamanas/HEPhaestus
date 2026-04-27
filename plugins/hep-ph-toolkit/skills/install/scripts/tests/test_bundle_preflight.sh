#!/usr/bin/env bash
# test_bundle_preflight.sh — assert all T1 acceptance criteria for bundle-preflight.
set -euo pipefail

# Change to the install/ directory (two levels up from this test file).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$INSTALL_DIR"

pass() { printf 'PASS: %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

# ── 1. demo bundle ───────────────────────────────────────────────────────────
H1=$(mktemp -d); X1=$(mktemp -d)
out1=$(HOME="$H1" XDG_CONFIG_HOME="$X1" bash scripts/demo-install.sh bundle-preflight demo)
python3 -c 'import json,sys; d=json.loads(sys.argv[1]); assert d["tools"]==["wolfram","sarah","spheno","mg5"], "tools mismatch: "+str(d["tools"])' "$out1" \
  || fail "demo: tools != [wolfram,sarah,spheno,mg5]"
pass "demo: tools==[wolfram,sarah,spheno,mg5]"

python3 -c 'import json,sys; d=json.loads(sys.argv[1]); assert d["requires_wolfram"]==True, "requires_wolfram mismatch"' "$out1" \
  || fail "demo: requires_wolfram != true"
pass "demo: requires_wolfram==true"

python3 -c 'import json,sys; d=json.loads(sys.argv[1]); assert d["wolfram_dependents"]==["sarah"], "wolfram_dependents mismatch: "+str(d["wolfram_dependents"])' "$out1" \
  || fail "demo: wolfram_dependents != [sarah]"
pass "demo: wolfram_dependents==[sarah]"

# ── 2. bsm-spectrum: wolfram_dependents exactly ["sarah"] (NOT ["sarah","feynrules"]) ──
H2=$(mktemp -d); X2=$(mktemp -d)
out2=$(HOME="$H2" XDG_CONFIG_HOME="$X2" bash scripts/demo-install.sh bundle-preflight bsm-spectrum)
python3 -c 'import json,sys; d=json.loads(sys.argv[1]); assert d["wolfram_dependents"]==["sarah"], "wolfram_dependents mismatch: "+str(d["wolfram_dependents"])' "$out2" \
  || fail "bsm-spectrum: wolfram_dependents != [sarah]"
pass "bsm-spectrum: wolfram_dependents==[sarah] (not [sarah,feynrules])"

# ── 3. dm-relic: requires_wolfram==false, wolfram_dependents==[] ─────────────
H3=$(mktemp -d); X3=$(mktemp -d)
out3=$(HOME="$H3" XDG_CONFIG_HOME="$X3" bash scripts/demo-install.sh bundle-preflight dm-relic)
python3 -c 'import json,sys; d=json.loads(sys.argv[1]); assert d["requires_wolfram"]==False, "requires_wolfram mismatch"' "$out3" \
  || fail "dm-relic: requires_wolfram != false"
pass "dm-relic: requires_wolfram==false"

python3 -c 'import json,sys; d=json.loads(sys.argv[1]); assert d["wolfram_dependents"]==[], "wolfram_dependents mismatch: "+str(d["wolfram_dependents"])' "$out3" \
  || fail "dm-relic: wolfram_dependents != []"
pass "dm-relic: wolfram_dependents==[]"

# ── 4. dm-narrow-resonance: wolfram_dependents==["drake"], requires_wolfram==true ──
H4=$(mktemp -d); X4=$(mktemp -d)
out4=$(HOME="$H4" XDG_CONFIG_HOME="$X4" bash scripts/demo-install.sh bundle-preflight dm-narrow-resonance)
python3 -c 'import json,sys; d=json.loads(sys.argv[1]); assert d["wolfram_dependents"]==["drake"], "wolfram_dependents mismatch: "+str(d["wolfram_dependents"])' "$out4" \
  || fail "dm-narrow-resonance: wolfram_dependents != [drake]"
pass "dm-narrow-resonance: wolfram_dependents==[drake]"

python3 -c 'import json,sys; d=json.loads(sys.argv[1]); assert d["requires_wolfram"]==True, "requires_wolfram mismatch"' "$out4" \
  || fail "dm-narrow-resonance: requires_wolfram != true"
pass "dm-narrow-resonance: requires_wolfram==true"

# ── 5. DM-NARROW-RESONANCE (uppercase) → same JSON as lowercase ──────────────
H5=$(mktemp -d); X5=$(mktemp -d)
out5=$(HOME="$H5" XDG_CONFIG_HOME="$X5" bash scripts/demo-install.sh bundle-preflight DM-NARROW-RESONANCE)
python3 -c '
import json, sys
a = json.loads(sys.argv[1])
b = json.loads(sys.argv[2])
assert a == b, "uppercase result differs from lowercase: "+str(a)+" vs "+str(b)
' "$out5" "$out4" || fail "DM-NARROW-RESONANCE: JSON differs from dm-narrow-resonance"
pass "DM-NARROW-RESONANCE: JSON equals lowercase dm-narrow-resonance result"

# ── 6. "  demo  " (whitespace) → same JSON as demo ───────────────────────────
H6=$(mktemp -d); X6=$(mktemp -d)
out6=$(HOME="$H6" XDG_CONFIG_HOME="$X6" bash scripts/demo-install.sh bundle-preflight "  demo  ")
python3 -c '
import json, sys
a = json.loads(sys.argv[1])
b = json.loads(sys.argv[2])
assert a == b, "trimmed result differs from plain demo: "+str(a)+" vs "+str(b)
' "$out6" "$out1" || fail '"  demo  ": JSON differs from demo'
pass '"  demo  ": JSON equals demo result (trimmed)'

# ── 7. bogus → exit 2; stderr contains error substrings ──────────────────────
H7=$(mktemp -d); X7=$(mktemp -d)
err7=""
rc7=0
err7=$(HOME="$H7" XDG_CONFIG_HOME="$X7" bash scripts/demo-install.sh bundle-preflight bogus 2>&1 >/dev/null) || rc7=$?
[ "$rc7" -eq 2 ] || fail "bogus: expected exit 2, got $rc7"
pass "bogus: exit 2"

printf '%s' "$err7" | grep -qF '"error":"unknown bundle: bogus"' \
  || fail 'bogus: stderr missing "error":"unknown bundle: bogus"'
pass 'bogus: stderr contains "error":"unknown bundle: bogus"'

printf '%s' "$err7" | grep -qF '"known":["demo","bsm-spectrum"' \
  || fail 'bogus: stderr missing "known":["demo","bsm-spectrum"'
pass 'bogus: stderr contains "known":["demo","bsm-spectrum"'

# ── 8. No-arg invocation → exit 2 ────────────────────────────────────────────
H8=$(mktemp -d); X8=$(mktemp -d)
rc8=0
HOME="$H8" XDG_CONFIG_HOME="$X8" bash scripts/demo-install.sh bundle-preflight 2>/dev/null || rc8=$?
[ "$rc8" -eq 2 ] || fail "no-arg: expected exit 2, got $rc8"
pass "no-arg bundle-preflight: exit 2"

# ── 9. Empty-string arg → exit 2; stderr contains error substring ────────────
H9=$(mktemp -d); X9=$(mktemp -d)
err9=""
rc9=0
err9=$(HOME="$H9" XDG_CONFIG_HOME="$X9" bash scripts/demo-install.sh bundle-preflight "" 2>&1 >/dev/null) || rc9=$?
[ "$rc9" -eq 2 ] || fail 'empty-arg: expected exit 2, got '"$rc9"
pass "empty-arg bundle-preflight: exit 2"

printf '%s' "$err9" | grep -qF '"error":"unknown bundle: "' \
  || fail 'empty-arg: stderr missing "error":"unknown bundle: "'
pass 'empty-arg: stderr contains "error":"unknown bundle: "'

# ── 10. Config-neutrality: no config.json created by bundle-preflight ─────────
HA=$(mktemp -d); XA=$(mktemp -d)
HOME="$HA" XDG_CONFIG_HOME="$XA" bash scripts/demo-install.sh bundle-preflight demo >/dev/null
if [ -f "$XA/hephaestus/config.json" ]; then
  fail "config-neutrality: config.json was created by bundle-preflight demo"
fi
pass "config-neutrality: config.json not created after bundle-preflight demo"

# ── 11. Syntax check: bash -n scripts/demo-install.sh ────────────────────────
bash -n scripts/demo-install.sh || fail "bash -n scripts/demo-install.sh failed"
pass "bash -n scripts/demo-install.sh: exit 0"

# ── 12. detect-all regression: 4 lines, each parseable JSON with a "tool" key ──
HB=$(mktemp -d); XB=$(mktemp -d)
detect_out=$(HOME="$HB" XDG_CONFIG_HOME="$XB" bash scripts/demo-install.sh detect-all)
line_count=$(printf '%s\n' "$detect_out" | wc -l | tr -d ' ')
[ "$line_count" -eq 4 ] || fail "detect-all: expected 4 lines, got $line_count"
pass "detect-all: returns 4 lines"

while IFS= read -r line; do
  python3 -c 'import json,sys; d=json.loads(sys.argv[1]); assert "tool" in d, "missing tool key"' "$line" \
    || fail "detect-all: line not parseable JSON with tool key: $line"
done <<< "$detect_out"
pass "detect-all: each line is parseable JSON with a tool key"

echo "All bundle-preflight tests passed."
