"""
config_helpers.py — Python mirror of _common.sh config_get / config_merge.

Single source of truth for reading/writing the hephaestus config.json.
Used by W3, W4, W5 Python scripts.

State and config roots (§2.3 of phase2-plan-final.md):
    STATE_ROOT  — per-model state, overridden by HEPPH_STATE_ROOT in tests
    CONFIG_DIR  — config directory, overridden via XDG_CONFIG_HOME in tests
    CONFIG_PATH — config.json path

Atomic write discipline (§2.6):
    Write to tmp, flush + fsync fd, os.rename (atomic POSIX), fsync parent dir.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import datetime
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Roots (env-override for test isolation)
# ---------------------------------------------------------------------------

STATE_ROOT: Path = Path(
    os.environ.get("HEPPH_STATE_ROOT")
    or (Path.home() / ".local" / "share" / "hephaestus")
)

CONFIG_DIR: Path = (
    Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    / "hephaestus"
)

CONFIG_PATH: Path = CONFIG_DIR / "config.json"

# ---------------------------------------------------------------------------
# Model-name regex (§2.12)
# ---------------------------------------------------------------------------

MODEL_NAME_REGEX = re.compile(r"^[a-z][a-z0-9_]{1,30}$")


def _reload_roots() -> None:
    """Re-compute module-level roots from env.  Call in tests after monkeypatch."""
    global STATE_ROOT, CONFIG_DIR, CONFIG_PATH
    STATE_ROOT = Path(
        os.environ.get("HEPPH_STATE_ROOT")
        or (Path.home() / ".local" / "share" / "hephaestus")
    )
    CONFIG_DIR = (
        Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
        / "hephaestus"
    )
    CONFIG_PATH = CONFIG_DIR / "config.json"


# ---------------------------------------------------------------------------
# Config I/O
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Return parsed config.json, or empty dict if the file is absent/corrupt."""
    # Always read the current CONFIG_PATH (may have been updated by _reload_roots)
    cfg = CONFIG_DIR / "config.json"
    if not cfg.exists():
        return {}
    try:
        with open(cfg) as f:
            return json.load(f)
    except Exception:
        return {}


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write(path: Path, data: dict) -> None:
    """Write *data* atomically to *path* with full fsync discipline.

    Steps (§2.6):
      1. Write to a tmp file in the same directory, flush + fsync fd.
      2. os.rename(tmp, path)  — atomic on POSIX.
      3. fsync the parent directory fd.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    dir_path = str(path.parent)
    # Use a tmp file in the same directory so rename is on the same filesystem
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.rename(tmp_path, str(path))
        dir_fd = os.open(dir_path, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        # Clean up tmp on failure; do not leave orphaned .tmp files
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def merge_config(**kwargs: str) -> None:
    """Atomically update config.json with the supplied key→value pairs.

    Preserves all unrelated keys.  Updates ``last_configured`` to UTC ISO 8601.
    """
    cfg = CONFIG_DIR / "config.json"
    data = load_config()
    for k, v in kwargs.items():
        data[k] = v
    data["last_configured"] = _utc_now()
    if not data.get("python"):
        data["python"] = shutil.which("python3") or ""
    _atomic_write(cfg, data)


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

def register_model(name: str, **fields: object) -> None:
    """Upsert ``config["models"][name]`` with *fields*.

    Raises ``ValueError`` if *name* does not match MODEL_NAME_REGEX.
    """
    if not MODEL_NAME_REGEX.match(name):
        raise ValueError(
            f"invalid model name {name!r}: must match ^[a-z][a-z0-9_]{{1,30}}$"
        )
    cfg = CONFIG_DIR / "config.json"
    data = load_config()
    models: dict = data.setdefault("models", {})
    entry: dict = models.setdefault(name, {})
    entry.update(fields)
    data["last_configured"] = _utc_now()
    if not data.get("python"):
        data["python"] = shutil.which("python3") or ""
    _atomic_write(cfg, data)


def get_model(name: str) -> dict | None:
    """Return the model sub-dict for *name*, or ``None`` if absent."""
    data = load_config()
    return data.get("models", {}).get(name)


# ---------------------------------------------------------------------------
# CLI shim (minimal; mainly for quick smoke tests)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="hephaestus config helpers")
    sub = parser.add_subparsers(dest="cmd")

    get_p = sub.add_parser("get", help="Read a top-level config key")
    get_p.add_argument("key")

    merge_p = sub.add_parser("merge", help="Merge key=value pairs into config")
    merge_p.add_argument("pairs", nargs="+", metavar="KEY=VALUE")

    args = parser.parse_args()

    if args.cmd == "get":
        val = load_config().get(args.key, "")
        print(val)
    elif args.cmd == "merge":
        kv: dict[str, str] = {}
        for pair in args.pairs:
            if "=" not in pair:
                print(f"error: expected KEY=VALUE, got {pair!r}", file=sys.stderr)
                sys.exit(1)
            k, v = pair.split("=", 1)
            kv[k] = v
        merge_config(**kv)
    else:
        parser.print_help()
        sys.exit(2)
