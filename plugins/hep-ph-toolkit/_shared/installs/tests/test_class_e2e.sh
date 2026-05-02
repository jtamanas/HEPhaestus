#!/usr/bin/env bash
# End-to-end smoke for the CLASS onboarding bundle (cosmology-linear).
#
# Requires:  HEPPH_RUN_NETWORK_TESTS=1   (gates network access)
#            cc, make, python3, Cython    (build toolchain)
#            Internet access to github.com/lesgourg/class_public
#
# Usage:     bash test_class_e2e.sh
# Exit:      0 = all checks pass
#            non-zero = first failing check
#
# Deferred: this test is TODO-OPUS-MANUAL on macOS/Darwin without a Linux+gcc
# environment.  Run on Ubuntu 22.04 LTS with system gcc and cython installed.
#
# Mirror: plugins/hep-ph-toolkit/_shared/installs/tests/test_detect_common.sh
set -euo pipefail

if [[ -z "${HEPPH_RUN_NETWORK_TESTS:-}" ]]; then
  echo "SKIP: HEPPH_RUN_NETWORK_TESTS not set — e2e test deferred (TODO-OPUS-MANUAL)" >&2
  exit 0
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
BUNDLE_INSTALL="$REPO_ROOT/plugins/hep-ph-toolkit/skills/install/scripts/bundle_install.sh"
RUN_CLASS="$REPO_ROOT/plugins/hep-ph-toolkit/skills/class/scripts/run_class.py"
SCHEMA="$REPO_ROOT/plugins/shared/schemas/cosmology.schema.json"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

export XDG_CONFIG_HOME="$TMP/xdg"
export HEPPH_STATE_ROOT="$TMP/state"
mkdir -p "$XDG_CONFIG_HOME/hephaestus" "$HEPPH_STATE_ROOT"

echo "=== Step 1: detect (should be missing before install) ==="
DETECT_OUT="$(bash "$REPO_ROOT/plugins/hep-ph-toolkit/_shared/installs/class/install.sh" detect 2>&1)"
echo "$DETECT_OUT"
echo "$DETECT_OUT" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='missing', d"
echo "PASS: detect shows missing"

echo "=== Step 2: bundle install (cosmology-linear) ==="
bash "$BUNDLE_INSTALL" --bundle cosmology-linear
echo "PASS: bundle_install completed"

echo "=== Step 3: detect (should be configured after install) ==="
DETECT_OUT2="$(bash "$REPO_ROOT/plugins/hep-ph-toolkit/_shared/installs/class/install.sh" detect 2>&1)"
echo "$DETECT_OUT2"
echo "$DETECT_OUT2" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='configured', d"
echo "PASS: detect shows configured"

echo "=== Step 4: run /class cmb planck18 ==="
OUT_DIR="$HEPPH_STATE_ROOT/e2e_cmb"
mkdir -p "$OUT_DIR"
python3 "$RUN_CLASS" cmb planck18 --output-dir "$OUT_DIR"
echo "PASS: run_class.py cmb planck18 completed"

echo "=== Step 5: cls.dat exists and has TSV header ==="
CLS_DAT="$OUT_DIR/cls.dat"
test -f "$CLS_DAT" || { echo "FAIL: cls.dat missing"; exit 1; }
head -1 "$CLS_DAT" | grep -q '^#' || { echo "FAIL: cls.dat missing TSV header"; exit 1; }
echo "PASS: cls.dat exists with header"

echo "=== Step 6: cosmology.json validates against schema ==="
COSMO_JSON="$OUT_DIR/cosmology.json"
test -f "$COSMO_JSON" || { echo "FAIL: cosmology.json missing"; exit 1; }
python3 -c "
import json, jsonschema, sys
d = json.load(open('$COSMO_JSON'))
s = json.load(open('$SCHEMA'))
jsonschema.Draft202012Validator(s).validate(d)
print('schema validation: PASS')
"
echo "PASS: cosmology.json valid against cosmology.schema.json"

echo ""
echo "=== ALL E2E CHECKS PASSED ==="
