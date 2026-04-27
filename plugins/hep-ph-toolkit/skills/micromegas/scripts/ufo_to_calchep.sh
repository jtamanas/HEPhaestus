#!/usr/bin/env bash
# ufo_to_calchep.sh — convert a UFO model directory to a micrOMEGAs CalcHEP project.
#
# Usage: ufo_to_calchep.sh <ufo_dir> <model_name> [--output <project_dir>]
#
# Cache key: sha256(tar(ufo_dir)) ++ micromegas_version ++ ufo_dialect
# Cache location: $STATE_ROOT/models/<model_name>/micromegas_project/cache/<hash>/
#
# Concurrency: bin/flock_run.sh (fcntl.flock) on a per-hash lockfile prevents parallel population.
# Cache directory population is write-to-<hash>.tmp then atomic mv.
#
# Exit codes:
#   0  — success, project dir printed to stdout
#   2  — UFO_CONVERT_FAILED (blocker on stderr)
#   3  — CALCHEP_CONVERTER_VERSION_SKEW (blocker on stderr)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
. "$SHARED_COMMON"

_LOG_TAG="micromegas-ufo"

EXIT_UFO_FAILED=2
EXIT_VERSION_SKEW=3

# ── Argument parsing ──────────────────────────────────────────────────────────
if [ $# -lt 2 ]; then
  err "Usage: ufo_to_calchep.sh <ufo_dir> <model_name> [--output <project_dir>]"
  exit $EXIT_UFO_FAILED
fi

ufo_dir="$1"
model_name="$2"
shift 2

output_dir=""
while [ $# -gt 0 ]; do
  case "$1" in
    --output) output_dir="$2"; shift 2 ;;
    *) err "Unknown arg: $1"; exit $EXIT_UFO_FAILED ;;
  esac
done

if [ ! -d "$ufo_dir" ]; then
  printf '{"code":"UFO_CONVERT_FAILED","mode":"fatal","message":"UFO directory not found: %s"}\n' \
    "$ufo_dir" >&2
  exit $EXIT_UFO_FAILED
fi

# ── Config ────────────────────────────────────────────────────────────────────
micromegas_path="$(config_get micromegas_path 2>/dev/null || true)"
micromegas_version="$(config_get micromegas_version 2>/dev/null || echo "6.0.5")"

if [ -z "$micromegas_path" ]; then
  printf '{"code":"MICROMEGAS_INPUT_MISSING","mode":"fatal","message":"micromegas_path not configured. Run /micromegas-install first."}\n' >&2
  exit $EXIT_UFO_FAILED
fi

# ── Determine UFO dialect ─────────────────────────────────────────────────────
ufo_dialect="1.x"
if [ -f "$ufo_dir/__init__.py" ]; then
  ufo_version_py="$(python3 -c "
import ast
with open('$ufo_dir/__init__.py') as f:
    src = f.read()
try:
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == 'UFO_VERSION':
                    if isinstance(node.value, ast.Constant):
                        print(node.value.value)
                        raise SystemExit(0)
except SystemExit:
    pass
print('1.x')
" 2>/dev/null || echo "1.x")"
  ufo_dialect="$ufo_version_py"
elif [ -f "$ufo_dir/restrict_default.dat" ]; then
  ufo_dialect="1.x"
fi

# ── Cache key ─────────────────────────────────────────────────────────────────
cache_hash="$(python3 - "$ufo_dir" "$micromegas_version" "$ufo_dialect" <<'PY'
import hashlib, os, sys, tarfile, io

ufo_dir, version, dialect = sys.argv[1], sys.argv[2], sys.argv[3]
h = hashlib.sha256()
# Hash directory contents deterministically
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w") as tar:
    tar.add(ufo_dir, arcname=os.path.basename(ufo_dir))
h.update(buf.getvalue())
h.update(version.encode())
h.update(dialect.encode())
print(h.hexdigest()[:32])
PY
)"

STATE_ROOT="${HEPPH_STATE_ROOT:-$HOME/.local/share/hephaestus}"
cache_base="$STATE_ROOT/models/$model_name/micromegas_project/cache"
lock_dir="$STATE_ROOT/.locks"
mkdir -p "$cache_base" "$lock_dir"

cache_dir="$cache_base/$cache_hash"
lock_file="$lock_dir/micromegas_cache_${cache_hash}.lock"

# ── flock-protected cache population ─────────────────────────────────────────
# Export all variables needed by the cache-population body so the child bash
# process (spawned by flock_run.sh's exec) can access them.
export cache_dir cache_hash cache_base ufo_dir micromegas_path model_name
export output_dir EXIT_UFO_FAILED SHARED_COMMON
(
  # Acquire exclusive lock via repo-vendored portable helper.
  # NOTE: Outer ( ... ) subshell preserved — fd 200's lifetime tracks subshell exit.
  exec 200>"$lock_file"
  HEPPH_REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null \
    || dirname "$(dirname "$(dirname "$(dirname "${BASH_SOURCE[0]}")")")")"

  # Helper exits 124 on timeout with FLOCK_TIMEOUT JSON; remap to UFO_CONVERT_FAILED
  # to preserve the existing blocker contract for downstream consumers.
  rc=0
  "$HEPPH_REPO_ROOT/bin/flock_run.sh" --fd 200 "$lock_file" 60 -- bash -c '
. "$SHARED_COMMON"
_LOG_TAG="micromegas-ufo"

if [ -d "$cache_dir" ] && [ -f "$cache_dir/.complete" ]; then
  log "Cache hit: $cache_dir"
else
  cache_tmp="$cache_base/${cache_hash}.tmp"
  rm -rf "$cache_tmp"
  log "Converting UFO model '"'"'$ufo_dir'"'"' to CalcHEP project..."
  if [ ! -f "$micromegas_path/newProject" ]; then
    printf '"'"'{"code":"UFO_CONVERT_FAILED","mode":"fatal","message":"micrOMEGAs newProject not found at %s"}\n'"'"' \
      "$micromegas_path/newProject" >&2
    exit $EXIT_UFO_FAILED
  fi
  mkdir -p "$cache_tmp"
  convert_log="$cache_tmp/convert.log"
  (
    cd "$cache_tmp"
    "$micromegas_path/newProject" "$model_name" 2>&1 | tee "$convert_log" || true
  )
  if [ -d "$cache_tmp/$model_name" ]; then
    cp -r "$ufo_dir"/* "$cache_tmp/$model_name/" 2>/dev/null || true
  else
    printf '"'"'{"code":"UFO_CONVERT_FAILED","mode":"fatal","message":"newProject did not create %s directory","context":{"convert_log_tail":"%s"}}\n'"'"' \
      "$model_name" "$(tail -10 "$convert_log" | tr '"'"'\n'"'"' '"'"'|'"'"' | sed '"'"'s/"/\\"/g'"'"')" >&2
    rm -rf "$cache_tmp"
    exit $EXIT_UFO_FAILED
  fi
  touch "$cache_tmp/.complete"
  mv "$cache_tmp" "$cache_dir"
  log "Cache populated: $cache_dir"
fi
if [ -n "$output_dir" ]; then
  cp -r "$cache_dir" "$output_dir" 2>/dev/null || true
  echo "$output_dir"
else
  echo "$cache_dir"
fi
' || rc=$?
  if [ "$rc" -eq 124 ]; then
    printf '{"code":"UFO_CONVERT_FAILED","mode":"fatal","message":"Lock timeout for cache hash %s"}\n' \
      "$cache_hash" >&2
    exit $EXIT_UFO_FAILED
  elif [ "$rc" -ne 0 ]; then
    exit "$rc"
  fi
)
