#!/usr/bin/env bash
# Probe the DDCalc mirror URL chain and return the first reachable URL.
# Usage: _probe_url.sh [--dry-run]
# Stdout (success): the first URL that returns HTTP 200 (via curl -sI -L --max-redirs 5)
# Exit 0 on success; exit non-zero with DDCALC_UPSTREAM_UNREACHABLE on exhaustion.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
. "$SHARED_COMMON"

_tag="ddcalc-probe-url"

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

SKILL_ENV="$SCRIPT_DIR/../skill_env.yaml"

# Parse mirror URLs from skill_env.yaml using Python
URLS="$(python3 - "$SKILL_ENV" <<'PY'
import yaml, sys
data = yaml.safe_load(open(sys.argv[1]))
mirrors = data.get("HEPPH_DDCALC_MIRROR_URLS", [data.get("HEPPH_DDCALC_URL", "")])
for u in mirrors:
    print(u)
PY
)"

if [ -z "$URLS" ]; then
  "$SCRIPT_DIR/_blocker.sh" DDCALC_UPSTREAM_UNREACHABLE \
    "No mirror URLs configured in skill_env.yaml" '{}' >&2
  exit "$EXIT_DOWNLOAD"
fi

_probe_one() {
  local url="$1"
  local status
  status="$(curl -sIL --max-redirs 5 --max-time 15 "$url" 2>/dev/null | \
    grep -E '^HTTP/' | tail -1 | awk '{print $2}' || echo '000')"
  echo "$status"
}

while IFS= read -r url; do
  [ -z "$url" ] && continue
  log "Probing: $url"
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "$url"
    exit 0
  fi
  status="$(_probe_one "$url")"
  log "  → HTTP $status"
  if [ "$status" = "200" ]; then
    echo "$url"
    exit 0
  fi
done <<< "$URLS"

"$SCRIPT_DIR/_blocker.sh" DDCALC_UPSTREAM_UNREACHABLE \
  "All DDCalc mirror URLs exhausted (no HTTP 200)" \
  "{\"tried_urls\":$(python3 -c "import json; urls='''$URLS'''.strip().split('\n'); print(json.dumps(urls))")}" >&2
exit "$EXIT_DOWNLOAD"
