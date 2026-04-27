#!/usr/bin/env bash
# _netguard.sh — PATH-override sandbox that traps network access during make.
#
# Usage:
#   source _netguard.sh
#   netguard_setup <log_file>
#   # ... run make inside $NETGUARD_PATH_PREFIX prepended to PATH ...
#   netguard_check <log_file>   # exits non-zero if any network access logged
#
# The sandbox stubs curl, wget, git with scripts that exit 42 and log the
# attempted access to <log_file>. Any entry in the log after make completes
# triggers MICROMEGAS_BUILD_NEEDS_NETWORK.
#
# Example:
#   . _netguard.sh
#   NETGUARD_TMP="$(mktemp -d)"
#   NETGUARD_LOG="$NETGUARD_TMP/net.log"
#   netguard_setup "$NETGUARD_LOG"
#   PATH="$NETGUARD_STUB_DIR:$PATH" make -C "$path" -j4 2>&1
#   netguard_check "$NETGUARD_LOG"

netguard_setup() {
  local log_file="$1"
  NETGUARD_STUB_DIR="$(mktemp -d)"
  NETGUARD_LOG_FILE="$log_file"
  > "$log_file"  # initialize empty

  for tool in curl wget git; do
    cat > "$NETGUARD_STUB_DIR/$tool" <<STUB
#!/usr/bin/env bash
echo "NETGUARD: $tool \$*" >> '$log_file'
exit 42
STUB
    chmod +x "$NETGUARD_STUB_DIR/$tool"
  done

  export NETGUARD_STUB_DIR NETGUARD_LOG_FILE
}

netguard_check() {
  local log_file="${1:-$NETGUARD_LOG_FILE}"
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  if [ ! -f "$log_file" ]; then return 0; fi
  if [ ! -s "$log_file" ]; then return 0; fi

  # Parse the first attempted URL from the log
  local first_entry
  first_entry="$(head -1 "$log_file")"
  local attempted_url
  attempted_url="$(echo "$first_entry" | grep -oE 'https?://[^ ]+' | head -1 || echo "")"

  # Source blocker helper if available
  if [ -f "$script_dir/_blocker.sh" ]; then
    . "$script_dir/_blocker.sh"
    emit_blocker MICROMEGAS_BUILD_NEEDS_NETWORK fatal \
      "micrOMEGAs build attempted network access under HEPPH_NO_NETWORK=1." \
      "The build tried to download packages. Pre-stage them in HEPPH_OFFLINE_CACHE_DIR." \
      "{\"attempted_url\":\"${attempted_url}\",\"netguard_log\":\"$(cat "$log_file" | head -5 | tr '\n' '|')\"}"
  else
    printf '{"code":"MICROMEGAS_BUILD_NEEDS_NETWORK","mode":"fatal","message":"Build tried network: %s"}\n' \
      "$attempted_url" >&2
  fi
  return 33  # EXIT_BUILD_NET
}

netguard_cleanup() {
  if [ -n "${NETGUARD_STUB_DIR:-}" ] && [ -d "$NETGUARD_STUB_DIR" ]; then
    rm -rf "$NETGUARD_STUB_DIR"
  fi
}
