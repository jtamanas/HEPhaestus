#!/usr/bin/env bash
# atomic_write.sh — atomic file-write helpers sourced by install scripts.
# Not executable on its own; source this file after _common.sh so log/err/warn
# are available.
#
# Public interface:
#   atomic_write <dest_path> <content_file>
#       Copy <content_file> → <dest_path> atomically (tmp + fsync + rename +
#       dir-fsync).  Exits non-zero on any failure.
#
#   atomic_write_stdin <dest_path>
#       Read content from stdin, same atomicity.

# Implementation note: uses a Python heredoc (Python ≥ 3.10) for fsync +
# rename + dir-fsync, matching the discipline already used in config_merge
# inside _common.sh.

_atomic_write_impl() {
  # _atomic_write_impl <dest_path> <src_path>
  local dest="$1" src="$2"
  python3 - "$dest" "$src" <<'PY'
import os, sys, pathlib

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

dest_path = sys.argv[1]
src_path  = sys.argv[2]

dest_dir  = str(pathlib.Path(dest_path).parent)
dest_name = pathlib.Path(dest_path).name
tmp_path  = os.path.join(dest_dir, f".atomic_write_{dest_name}.tmp")

try:
    with open(src_path, "rb") as src_f:
        data = src_f.read()

    with open(tmp_path, "wb") as tmp_f:
        tmp_f.write(data)
        tmp_f.flush()
        os.fsync(tmp_f.fileno())

    os.rename(tmp_path, dest_path)

    dir_fd = os.open(dest_dir, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
except Exception as e:
    # Clean up tmp on error.
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    print(f"atomic_write error: {e}", file=sys.stderr)
    sys.exit(1)
PY
}

# atomic_write <dest_path> <content_file>
atomic_write() {
  local dest="$1" content_file="$2"
  if [ ! -r "$content_file" ]; then
    err "atomic_write: content_file not readable: $content_file"
    return 1
  fi
  _atomic_write_impl "$dest" "$content_file"
}

# atomic_write_stdin <dest_path>
atomic_write_stdin() {
  local dest="$1"
  local tmp_stdin
  tmp_stdin="$(mktemp)"
  cat > "$tmp_stdin"
  _atomic_write_impl "$dest" "$tmp_stdin"
  local rc=$?
  rm -f "$tmp_stdin"
  return $rc
}
