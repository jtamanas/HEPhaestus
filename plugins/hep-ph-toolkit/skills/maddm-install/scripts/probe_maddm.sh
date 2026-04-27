#!/usr/bin/env bash
# probe_maddm.sh — smoke test for a MadDM install.
#
# Verifies:
#   1. <maddm_path>/__init__.py exists (plugin entrypoint)
#   2. <MG5_ROOT>/bin/maddm is executable (launcher shim)
#   3. <maddm_path>/version parses to a semver-ish string
#
# Usage:
#   probe_maddm.sh <maddm_plugin_dir> [<mg5_root>]
#
# Outputs the version string on stdout (e.g. "3.2.13"). Returns non-zero on
# failure; callers are expected to translate that into a blocker if appropriate.
set -euo pipefail

maddm_dir="${1:-}"
mg5_root="${2:-}"

if [ -z "$maddm_dir" ]; then
  echo "probe_maddm.sh: missing maddm plugin dir argument" >&2
  exit 2
fi

# Derive MG5 root from maddm_dir if not provided: <MG5_ROOT>/PLUGIN/maddm.
if [ -z "$mg5_root" ]; then
  mg5_root="$(cd "$maddm_dir/../.." 2>/dev/null && pwd || true)"
fi

# Check 1: entrypoint file.
if [ ! -f "$maddm_dir/__init__.py" ]; then
  echo "probe_maddm.sh: missing $maddm_dir/__init__.py" >&2
  exit 1
fi

# Check 2: launcher shim. The canonical MadDM entry point is
# `mg5_aMC --mode=maddm`, which doesn't need the shim. A `<MG5_ROOT>/bin/maddm`
# shim is convenient when users want to invoke MadDM directly, so the
# git-install fallback path creates one, but neither MG5's native
# `install maddm` nor a fresh upstream checkout ships one. Warn, don't fail.
if [ -n "$mg5_root" ] && [ -d "$mg5_root" ] && [ ! -x "$mg5_root/bin/maddm" ]; then
  echo "probe_maddm.sh: NOTE: $mg5_root/bin/maddm shim not present (MadDM still callable via 'mg5_aMC --mode=maddm')." >&2
fi

# Check 3: version file. Parse the first semver-ish token.
version=""
if [ -f "$maddm_dir/version" ]; then
  version="$(grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' "$maddm_dir/version" | head -n1 || true)"
fi

# Fallback: scan __init__.py header for a version tag.
if [ -z "$version" ]; then
  version="$(grep -Eo 'MadDM[[:space:]]+v?[0-9]+\.[0-9]+\.[0-9]+' "$maddm_dir/__init__.py" 2>/dev/null \
              | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)"
fi

if [ -z "$version" ]; then
  echo "probe_maddm.sh: could not parse MadDM version from $maddm_dir" >&2
  exit 1
fi

# Check 4: syntax sweep. MadDM 3.2.13 upstream is Python 2 and needs the
# install-script patches (see install.sh apply_maddm_upstream_patches).
# This sweep catches:
#   - A user who points use-path at an unpatched tree and bypasses the
#     patch step (shouldn't happen now that use-path calls patches, but is
#     still the authoritative gate).
#   - Future upstream drift that 2to3 can't resolve (e.g. f-string
#     requirements on a pre-3.6 syntax residue).
# The sweep uses the ambient python3 (the interpreter MG5 runs under).
# Skips files under EffOperators/{COMPLEX,REAL}/ because those trees are
# generator artefacts (generated UFO model helpers), not loaded at plugin
# import time; including them would flag every regenerated UFO.
sweep_errors="$(
  find "$maddm_dir" -name '*.py' \
      -not -path '*/__pycache__/*' \
      -not -path '*/EffOperators/*' \
      -print0 \
    | xargs -0 -n1 python3 -c '
import ast, sys
try:
    ast.parse(open(sys.argv[1]).read())
except SyntaxError as e:
    msg = (e.msg or "")[:60]
    print(f"{sys.argv[1]}:{e.lineno}: {msg}")
' 2>&1
)"
if [ -n "$sweep_errors" ]; then
  echo "probe_maddm.sh: Python syntax errors remain under $maddm_dir:" >&2
  printf '%s\n' "$sweep_errors" | head -n 10 >&2
  exit 1
fi

printf '%s\n' "$version"
