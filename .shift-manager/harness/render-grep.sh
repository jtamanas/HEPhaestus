#!/usr/bin/env bash
# render-grep.sh — G-RENDERED-GREP harness (repo-level, portable, cross-skill)
#
# Usage: render-grep.sh <markdown-path> <fixed-string>
#
# Pipeline (in order):
#   1. python -m markdown <path>  — vanilla, no extensions; failure → exit 2
#   2. re.sub(r"<!--.*?-->", "", s, flags=re.S)   — strip HTML comments
#   3. re.sub(r"<[^>]+>", "", s)                   — strip HTML tags
#   4. re.sub(r"\s+", " ", s).strip()              — normalize whitespace (single-line contract)
#   5. grep -F -- "<fixed-string>"                  — case-sensitive substring match
#
# Exit codes:
#   0 = banner string present in rendered visible text
#   1 = banner string absent
#   2 = renderer error (python -m markdown failed or import error)
#
# Stdout on PASS: matching grep -F line(s)
# Stderr: silent unless exit 2
# No mutation, no network, deterministic.

set -euo pipefail

if [ $# -lt 2 ]; then
    echo "Usage: $0 <markdown-path> <fixed-string>" >&2
    exit 2
fi

MDPATH="$1"
NEEDLE="$2"

if [ ! -f "$MDPATH" ]; then
    echo "render-grep.sh: file not found: $MDPATH" >&2
    exit 2
fi

# Render markdown → strip comments → strip tags → normalize whitespace → grep
python3 - "$MDPATH" "$NEEDLE" <<'PYEOF'
import sys
import re
import subprocess

mdpath = sys.argv[1]
needle = sys.argv[2]

# Step 1: render with python -m markdown (vanilla, no extensions)
try:
    result = subprocess.run(
        [sys.executable, "-m", "markdown", mdpath],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    if result.returncode != 0:
        sys.stderr.write("render-grep.sh: python -m markdown failed:\n" + result.stderr)
        sys.exit(2)
    html = result.stdout
except Exception as e:
    sys.stderr.write("render-grep.sh: renderer error: " + str(e) + "\n")
    sys.exit(2)

# Step 2: strip HTML comments
s = re.sub(r"<!--.*?-->", "", html, flags=re.S)

# Step 3: strip HTML tags
s = re.sub(r"<[^>]+>", "", s)

# Step 4: normalize whitespace (single-line contract)
s = re.sub(r"\s+", " ", s).strip()

# Step 5: grep -F (case-sensitive substring)
if needle in s:
    # Print the matching context (single normalized line)
    print(s)
    sys.exit(0)
else:
    sys.exit(1)
PYEOF
