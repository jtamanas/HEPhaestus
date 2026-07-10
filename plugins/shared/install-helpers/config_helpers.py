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
# latest_slha provenance guard (§ frozen-SI staleness handoff, scope note #2)
# ---------------------------------------------------------------------------
#
# ``latest_slha`` is a *convenience cache*: a single per-model pointer to the
# most recently written SLHA spectrum. It is easy to trust stale: a later run
# for a DIFFERENT parameter point overwrites the pointer, and nothing records
# which point the file on disk actually corresponds to. ``register_latest_slha``
# records provenance alongside the pointer (a content fingerprint plus the
# point/params it was produced for); ``read_latest_slha`` warns loudly when the
# on-disk file drifted from the fingerprint or the caller asked for a different
# point than the cache holds. Both are additive and backward compatible:
# configs written before this guard simply lack the ``latest_slha_provenance``
# sibling, and reads then warn that provenance is unavailable rather than crash.


def _sha256_file(path: Path) -> str | None:
    """Return the hex sha256 of *path*, or None if it cannot be read."""
    import hashlib

    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def register_latest_slha(
    model: str,
    slha_path: str,
    point: str | None = None,
    params: dict | None = None,
    **extra_fields: object,
) -> None:
    """Record ``latest_slha`` for *model* together with provenance.

    Writes ``models[model]["latest_slha"]`` (the convenience-cache pointer) and
    a sibling ``models[model]["latest_slha_provenance"]`` dict:

        {"path", "sha256", "point", "params", "recorded_at"}

    ``point`` is any caller-side identifier for the parameter point/benchmark
    (e.g. a label); ``params`` is the key physics inputs (e.g. MS/MPsi/theta).
    Either may be None when the caller does not have it — provenance still
    records the content fingerprint so a later drift is detectable. Additional
    ``extra_fields`` are upserted onto the model entry unchanged (e.g.
    ``spheno_bin``, ``latest_run``), so this can replace a plain
    ``register_model(..., latest_slha=...)`` call.
    """
    resolved = str(Path(slha_path).resolve())
    provenance = {
        "path": resolved,
        "sha256": _sha256_file(Path(resolved)),
        "point": point,
        "params": params,
        "recorded_at": _utc_now(),
    }
    register_model(
        model,
        latest_slha=resolved,
        latest_slha_provenance=provenance,
        **extra_fields,
    )


def read_latest_slha(
    model: str,
    expected_point: str | None = None,
    expected_params: dict | None = None,
) -> str | None:
    """Return ``latest_slha`` for *model*, warning loudly on any mismatch.

    ``latest_slha`` is a convenience cache. This reader returns the recorded
    path (or None if unset) and prints a loud ``WARNING:`` line to stderr when:

      * the model or pointer is absent;
      * no provenance was recorded (pre-guard config — cannot verify);
      * the on-disk file's sha256 no longer matches the recorded fingerprint
        (the card changed under the pointer);
      * ``expected_point`` / ``expected_params`` are given and differ from the
        point/params the cache was recorded for (the pointer holds a different
        parameter point than the caller wants).

    Warnings never raise — the path is still returned so callers can decide.
    Every warning names the model and the recorded point so mismatches are
    self-describing.
    """
    def _warn(msg: str) -> None:
        print(f"WARNING: latest_slha[{model!r}] convenience cache: {msg}",
              file=sys.stderr)

    entry = get_model(model)
    if not entry:
        _warn("model not found in config; no cached SLHA.")
        return None

    path = entry.get("latest_slha")
    if not path:
        _warn("no latest_slha pointer recorded for this model.")
        return None

    prov = entry.get("latest_slha_provenance")
    if not prov:
        _warn(
            "no provenance recorded (config predates the provenance guard); "
            "cannot verify the file matches any parameter point. Re-run the "
            "spectrum writer to record provenance."
        )
        return path

    recorded_point = prov.get("point")
    recorded_sha = prov.get("sha256")

    # Content drift: did the file change under the pointer?
    if recorded_sha is not None:
        current_sha = _sha256_file(Path(path))
        if current_sha is None:
            _warn(
                f"recorded for point {recorded_point!r} but the file at {path} "
                "cannot be read now (moved/deleted)."
            )
        elif current_sha != recorded_sha:
            _warn(
                f"the SLHA file at {path} changed under the pointer "
                f"(sha256 {current_sha[:12]}... != recorded {recorded_sha[:12]}"
                f"...); it may no longer correspond to point "
                f"{recorded_point!r}."
            )

    # Point / params mismatch: is the cache the point the caller wants?
    if expected_point is not None and expected_point != recorded_point:
        _warn(
            f"caller requested point {expected_point!r} but the cache holds "
            f"point {recorded_point!r}; use a per-point SLHA path, not the "
            "convenience cache."
        )
    if expected_params is not None:
        recorded_params = prov.get("params")
        if recorded_params != expected_params:
            _warn(
                f"caller requested params {expected_params!r} but the cache "
                f"holds params {recorded_params!r} (point {recorded_point!r})."
            )

    return path


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
