#!/usr/bin/env bash
# Shared helpers sourced by install_{wolfram,sarah,spheno,mg5}.sh and install.sh.
# Not executable on its own.
#
# Single source of truth: this file lives at plugins/shared/install-helpers/_common.sh.
# The copy at plugins/hep-ph-toolkit/skills/install/scripts/_common.sh is a one-line shim.
# Only W0 (workstream/w0-shared-contracts) edits this file.
#
# Sourcing pattern for model-building skills (4 levels deep):
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
#   if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
#   . "$SHARED_COMMON"
#
# Sourcing pattern for hep-ph-demo scripts (3 levels deep):
#   . "$SCRIPT_DIR/../../../shared/install-helpers/_common.sh"
set -euo pipefail

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
CONFIG_FILE="$CONFIG_DIR/config.json"

# Shared exit codes. Per-tool scripts add local codes above 20.
EXIT_OK=0
EXIT_GENERIC=1
EXIT_NO_GFORTRAN=10
EXIT_NO_DISK=11
EXIT_DOWNLOAD=12
EXIT_CHECKSUM=13
EXIT_EXTRACT=14
EXIT_SMOKE=15
EXIT_BAD_PATH=16
EXIT_NO_WOLFRAM=20
EXIT_NO_UNZIP=21
EXIT_SARAH_PATH=22
EXIT_SPHENO_MAKE=23
EXIT_WOLFRAM_ACTIVATION=24
EXIT_NO_LAPACK=25
EXIT_NO_CMAKE=26
EXIT_NO_PYBIND=27
EXIT_FORM_BUILD=28
EXIT_LOOPTOOLS_BUILD=29
EXIT_CLASS_BUILD=30
EXIT_NOT_CONFIGURED=17

_tag="${_LOG_TAG:-install}"

log()  { printf '[%s] %s\n' "$_tag" "$*" >&2; }
warn() { printf '[%s] WARN: %s\n' "$_tag" "$*" >&2; }
err()  { printf '[%s] ERROR: %s\n' "$_tag" "$*" >&2; }

os_name() {
  case "$(uname -s)" in
    Darwin) echo macos ;;
    Linux)  echo linux ;;
    *)      echo other ;;
  esac
}

# Require N GB free under $HOME, else abort with $EXIT_NO_DISK.
# Usage: check_disk <min_gb> [<warn_gb>]
check_disk() {
  local min_gb="${1:-2}"
  local warn_gb
  # HEPPH_DISK_MIN_GB: test knob; overrides ALL check_disk callers. Document in docstring for reviewers. See P2 §2.2.
  if [ -n "${HEPPH_DISK_MIN_GB:-}" ]; then
    min_gb="$HEPPH_DISK_MIN_GB"
    warn_gb="$((min_gb * 2))"
  else
    warn_gb="${2:-$((min_gb * 2))}"
  fi
  local avail_kb avail_gb
  avail_kb=$(df -k "$HOME" | awk 'NR==2 {print $4}')
  avail_gb=$(( avail_kb / 1024 / 1024 ))
  if [ "$avail_gb" -lt "$min_gb" ]; then
    err "Need >${min_gb} GB free in \$HOME; have ${avail_gb} GB."
    exit "$EXIT_NO_DISK"
  fi
  if [ "$avail_gb" -lt "$warn_gb" ]; then
    warn "Low disk (${avail_gb} GB). Install may succeed but space is tight."
  fi
}

# Shared placeholder-SHA256 pattern (warn-not-abort when value is "TODO").
# Usage: verify_checksum <file> <expected-sha256-or-TODO>
verify_checksum() {
  local file="$1" expected="$2"
  if [ "$expected" = "TODO" ]; then
    warn "SHA256 is a placeholder (TODO) for $file. Skipping verification."
    warn "Before v1 release, compute the real checksum and update skill_env.yaml + the install script."
    return 0
  fi
  local got
  if command -v sha256sum >/dev/null 2>&1; then
    got=$(sha256sum "$file" | awk '{print $1}')
  else
    got=$(shasum -a 256 "$file" | awk '{print $1}')
  fi
  if [ "$got" != "$expected" ]; then
    err "SHA256 mismatch for $file. expected=$expected got=$got"
    exit $EXIT_CHECKSUM
  fi
  log "SHA256 OK for $(basename "$file")."
}

# Download <url> to <dest> with one automatic retry. Exits $EXIT_DOWNLOAD on repeat failure.
# Usage: download_with_retry <url> <dest> [<tool_prefix>]
# When HEPPH_NO_NETWORK=1: skip curl and serve from $HEPPH_OFFLINE_CACHE_DIR instead.
download_with_retry() {
  local url="$1" dest="$2" tool_prefix="${3:-DOWNLOAD}"
  local basename
  basename="$(basename "$dest")"

  # ── Offline-cache mode ────────────────────────────────────────────────────
  if [ "${HEPPH_NO_NETWORK:-0}" = "1" ]; then
    local cache_dir="${HEPPH_OFFLINE_CACHE_DIR:?HEPPH_OFFLINE_CACHE_DIR must be set when HEPPH_NO_NETWORK=1}"
    local cached="$cache_dir/$basename"
    if [ -r "$cached" ]; then
      log "Offline cache hit: $cached → $dest"
      cp "$cached" "$dest"
      return 0
    fi
    # Cache miss — emit blocker JSON on stderr and exit.
    printf '{"code":"%s_OFFLINE_CACHE_MISS","mode":"fatal","message":"Offline mode active but %s not found in cache","context":{"url":"%s","cache_dir":"%s","expected_basename":"%s"}}\n' \
      "$tool_prefix" "$basename" "$url" "$cache_dir" "$basename" >&2
    exit $EXIT_DOWNLOAD
  fi

  # ── Network mode (default) ────────────────────────────────────────────────
  local attempt
  for attempt in 1 2; do
    log "Download attempt $attempt: $url"
    if curl -L --fail --progress-bar -o "$dest" "$url"; then
      return 0
    fi
    warn "Download failed on attempt $attempt."
    rm -f "$dest"
  done
  err "Download failed twice. URL: $url"
  exit $EXIT_DOWNLOAD
}

# Read one JSON string field from the config, or print empty.
config_get() {
  local key="$1"
  [ -f "$CONFIG_FILE" ] || { echo ""; return 0; }
  python3 - "$CONFIG_FILE" "$key" <<'PY' 2>/dev/null || echo ""
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    print(d.get(sys.argv[2], "") or "")
except Exception:
    print("")
PY
}

# Atomically merge a set of key=value pairs into $CONFIG_FILE.
# Usage: config_merge key1 val1 key2 val2 ...
#
# Lock discipline (wired in by tier1/t12):
#   Acquires fcntl.flock(LOCK_EX) on $CONFIG_DIR/.config.lock before the
#   read-modify-write so concurrent callers serialize correctly.
#   bin/config_write_locked.sh is the recommended public entry point; direct
#   callers are also safe because the lock is re-entrant at the process level.
#
# fsync discipline (fixes pre-existing bug):
#   1. Write new content to a tmp file, flush + fsync the file descriptor.
#   2. os.rename(tmp, cfg) — atomic on POSIX.
#   3. fsync the parent directory fd to persist the directory entry.
config_merge() {
  mkdir -p "$CONFIG_DIR"
  local _lock_file="$CONFIG_DIR/.config.lock"
  touch "$_lock_file"
  local tmp
  tmp="$(mktemp "${CONFIG_FILE}.tmp.XXXXXX")"
  python3 - "$CONFIG_FILE" "$tmp" "$_lock_file" "$@" <<'PY'
import fcntl, json, os, sys, datetime, time

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

cfg_path, tmp_path, lock_path = sys.argv[1], sys.argv[2], sys.argv[3]
pairs = sys.argv[4:]
if len(pairs) % 2 != 0:
    print("config_merge: odd number of args", file=sys.stderr)
    sys.exit(1)

# Lock discipline: acquire fcntl.flock unless caller already holds the lock
# (signalled by HEPPH_CONFIG_LOCK_HELD=1, set by bin/config_write_locked.sh).
# This prevents nested-flock deadlock while ensuring all direct callers are
# also serialized.
lock_held_by_caller = os.environ.get("HEPPH_CONFIG_LOCK_HELD", "") == "1"
_lock_fd = None
if not lock_held_by_caller:
    _lock_fd = open(lock_path, "r+")
    deadline = time.monotonic() + 30
    while True:
        try:
            fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                print("config_merge: CONFIG_LOCK_TIMEOUT after 30s", file=sys.stderr)
                _lock_fd.close()
                sys.exit(1)
            time.sleep(0.05)

try:
    data = {}
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path) as f:
                data = json.load(f)
        except Exception:
            data = {}
    for i in range(0, len(pairs), 2):
        data[pairs[i]] = pairs[i + 1]
    data["last_configured"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if "python" not in data or not data["python"]:
        import shutil
        data["python"] = shutil.which("python3") or ""
    # Atomic write: write + fsync fd, rename, fsync parent dir
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.rename(tmp_path, cfg_path)
    dir_fd = os.open(os.path.dirname(os.path.abspath(cfg_path)), os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
finally:
    if _lock_fd is not None:
        fcntl.flock(_lock_fd, fcntl.LOCK_UN)
        _lock_fd.close()
PY
  local _rc=$?
  if [ $_rc -ne 0 ]; then
    rm -f "$tmp"
    return $_rc
  fi
  log "Updated config: $CONFIG_FILE"
}

# Probe the macOS SDK for LoopTools/FormCalc build compatibility.
# On non-Darwin: prints {"looptools_quad": true, "sdkroot": "", "ldflags": ""} and returns 0.
# On Darwin:
#   - probes gfortran -print-file-name=libquadmath.dylib to detect quad support.
#   - uses xcrun --show-sdk-path for sdkroot.
#   - Clang >= 15 on arm64 → ldflags: "-Wl,-ld_classic" else "".
#   - arm64 + missing libquadmath.dylib → looptools_quad: false.
# Emits one-line JSON to stdout.
check_macos_sdk() {
  local os_sys
  os_sys="$(uname -s)"
  if [ "$os_sys" != "Darwin" ]; then
    printf '{"looptools_quad": true, "sdkroot": "", "ldflags": ""}\n'
    return 0
  fi

  local arch
  arch="$(uname -m)"

  # Determine sdkroot.
  local sdkroot=""
  if command -v xcrun >/dev/null 2>&1; then
    sdkroot="$(xcrun --show-sdk-path 2>/dev/null || true)"
  fi

  # Probe libquadmath availability.
  local quad=true
  if [ "$arch" = "arm64" ]; then
    local quad_path=""
    if command -v gfortran >/dev/null 2>&1; then
      quad_path="$(gfortran -print-file-name=libquadmath.dylib 2>/dev/null || true)"
    fi
    # gfortran returns the name unchanged if not found.
    if [ -z "$quad_path" ] || [ "$quad_path" = "libquadmath.dylib" ] || [ ! -f "$quad_path" ]; then
      quad=false
    fi
  fi

  # Determine ldflags: arm64 + Clang >= 15 → -Wl,-ld_classic.
  local ldflags=""
  if [ "$arch" = "arm64" ]; then
    local clang_ver=""
    if command -v clang >/dev/null 2>&1; then
      clang_ver="$(clang --version 2>/dev/null | grep -Eo 'version [0-9]+' | head -n1 | awk '{print $2}' || true)"
    fi
    if [ -n "$clang_ver" ] && [ "$clang_ver" -ge 15 ] 2>/dev/null; then
      ldflags="-Wl,-ld_classic"
    fi
  fi

  printf '{"looptools_quad": %s, "sdkroot": "%s", "ldflags": "%s"}\n' \
    "$quad" "$sdkroot" "$ldflags"
}

# Portable timeout wrapper for verify bodies.
# Usage: with_timeout <seconds> <cmd> [args...]
# Returns 124 on timeout (matches GNU timeout convention).
with_timeout() {
  local seconds="$1"; shift
  local rc=0
  ( "$@" ) &
  local pid=$!
  ( sleep "$seconds" && kill -TERM "$pid" 2>/dev/null && sleep 1 && kill -KILL "$pid" 2>/dev/null ) &
  local killer=$!
  wait "$pid" 2>/dev/null
  rc=$?
  kill "$killer" 2>/dev/null || true
  wait "$killer" 2>/dev/null || true
  # Distinguish timeout-kill from natural non-zero:
  # - If killed by SIGTERM, wait returns 143 (128+15).
  # - If killed by SIGKILL, wait returns 137 (128+9).
  if [ "$rc" = "143" ] || [ "$rc" = "137" ]; then
    return 124
  fi
  return "$rc"
}
