#!/usr/bin/env python3
"""Ensure matplotlib and numpy are importable in the configured Python.

/hep-plot and friends assume ``config["python"]`` has matplotlib and numpy
installed. Rather than letting a plotting run crash at Step 4d of /demo, the
install skill verifies importability up front and pip-installs the missing
packages — then records versions + a timestamp in the shared config.

Behavior
--------
1. Resolve the target interpreter (``--python``, else ``config["python"]``,
   else ``shutil.which("python3")``).
2. Probe it for ``import matplotlib`` and ``import numpy``; collect versions.
3. If either is missing, shell out to ``<python> -m pip install matplotlib
   numpy`` (pinned ``matplotlib>=3.8`` per the plotting matplotlib pin).
4. Re-probe; if either is still unimportable, exit non-zero with a clear
   error — callers MUST NOT silently continue.
5. On success, merge ``matplotlib_version``, ``numpy_version``,
   ``python_deps_checked_at`` into the shared config atomically.

Exit codes
----------
  0  both deps importable (with or without a pip install)
  1  pip install exited non-zero
  2  pip install returned 0 but re-probe still fails
  3  interpreter missing / not executable
  4  no python interpreter could be resolved
 32  unexpected internal error
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEPS: tuple[tuple[str, str], ...] = (
    # (import_name, pip_spec). Pip specs keep the README's minimum version
    # contract; numpy has no explicit floor in hep-plotting/README.md.
    ("matplotlib", "matplotlib>=3.8"),
    ("numpy", "numpy"),
)

# Config-key prefix per package. Matches existing *_version / *_installed_at
# conventions elsewhere in the shared config.
VERSION_KEY = {"matplotlib": "matplotlib_version", "numpy": "numpy_version"}
TIMESTAMP_KEY = "python_deps_checked_at"


def default_config_path() -> Path:
    return (
        Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
        / "hephaestus"
        / "config.json"
    )


# ---------------------------------------------------------------------------
# IO helpers (kept small for test injection)
# ---------------------------------------------------------------------------


def load_config(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        with path.open() as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def write_config(path: Path, data: dict) -> None:
    """Atomic write. Mirrors _common.sh's config_merge fsync discipline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.rename(tmp, path)
    try:
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        # Best-effort directory fsync; don't fail the run on exotic filesystems.
        pass


def iso_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Probe / install primitives
# ---------------------------------------------------------------------------


def resolve_python(explicit: str | None, cfg: dict) -> str | None:
    """Pick the interpreter to operate on."""
    if explicit:
        return explicit
    if cfg.get("python"):
        return cfg["python"]
    which = shutil.which("python3")
    return which or None


def probe_versions(python: str, runner=None) -> dict[str, str | None]:
    """Return {pkg_name: version_str_or_None} by importing each dep in *python*.

    Uses a single subprocess that emits JSON so we can distinguish
    ImportError (value=None) from a working import (value="X.Y.Z").
    """
    if runner is None:
        runner = subprocess.run
    probe = (
        "import json, importlib\n"
        "out = {}\n"
        "for name in " + repr([n for n, _ in DEPS]) + ":\n"
        "    try:\n"
        "        m = importlib.import_module(name)\n"
        "        out[name] = getattr(m, '__version__', '') or ''\n"
        "    except Exception:\n"
        "        out[name] = None\n"
        "print(json.dumps(out))\n"
    )
    result = runner(
        [python, "-c", probe],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        # Interpreter itself is broken; treat every dep as missing.
        return {name: None for name, _ in DEPS}
    try:
        return json.loads(result.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {name: None for name, _ in DEPS}


def pip_install(python: str, specs: list[str], runner=None) -> int:
    """Shell out to ``<python> -m pip install <specs>``; return exit code."""
    if runner is None:
        runner = subprocess.run
    result = runner(
        [python, "-m", "pip", "install", *specs],
        capture_output=True,
        text=True,
        check=False,
    )
    # Surface pip output on stderr for the operator, pass/fail in rc.
    if result.stderr:
        sys.stderr.write(result.stderr)
    if result.stdout:
        sys.stdout.write(result.stdout)
    return result.returncode


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


class PythonDepsError(RuntimeError):
    """Raised when matplotlib/numpy cannot be made importable."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def ensure_python_deps(
    python: str | None,
    config_path: Path,
    *,
    runner=None,
    now=None,
) -> dict:
    """Ensure matplotlib + numpy importable in *python*; update *config_path*.

    Returns the updated config dict on success. Raises PythonDepsError with
    a specific exit_code on failure — callers MUST NOT swallow this.
    """
    if runner is None:
        runner = subprocess.run
    if now is None:
        now = iso_now
    cfg = load_config(config_path)
    py = resolve_python(python, cfg)
    if not py:
        raise PythonDepsError(
            "No Python interpreter resolved: pass --python, set config.python, "
            "or make python3 available on PATH.",
            exit_code=4,
        )
    if not (os.path.isabs(py) and os.access(py, os.X_OK)) and shutil.which(py) is None:
        raise PythonDepsError(
            f"Python interpreter not executable: {py}",
            exit_code=3,
        )

    versions = probe_versions(py, runner=runner)
    missing = [name for name, v in versions.items() if v is None]

    if missing:
        specs = [spec for name, spec in DEPS if name in missing]
        print(
            f"[install] Missing Python deps for {py}: {', '.join(missing)}. "
            f"Installing via pip: {' '.join(specs)}",
            file=sys.stderr,
        )
        rc = pip_install(py, specs, runner=runner)
        if rc != 0:
            raise PythonDepsError(
                f"pip install failed (exit {rc}) for {py}: {' '.join(specs)}",
                exit_code=1,
            )
        versions = probe_versions(py, runner=runner)
        still_missing = [name for name, v in versions.items() if v is None]
        if still_missing:
            raise PythonDepsError(
                "pip install returned 0 but these packages are still not "
                f"importable in {py}: {', '.join(still_missing)}. "
                "Check for a broken venv or a user-site vs system-site mismatch.",
                exit_code=2,
            )

    cfg = load_config(config_path)  # re-read to avoid racing other writers
    for name, version in versions.items():
        cfg[VERSION_KEY[name]] = version or ""
    cfg[TIMESTAMP_KEY] = now()
    if not cfg.get("python"):
        cfg["python"] = py
    write_config(config_path, cfg)
    return cfg


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--python", default=None, help="python interpreter to check")
    ap.add_argument(
        "--config",
        type=Path,
        default=default_config_path(),
        help="shared config path",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="emit a one-line JSON summary on stdout",
    )
    args = ap.parse_args(argv)

    try:
        cfg = ensure_python_deps(args.python, args.config)
    except PythonDepsError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"FAIL: {exc}", file=sys.stderr)
        return exc.exit_code

    summary = {
        "ok": True,
        "python": cfg.get("python", ""),
        "matplotlib_version": cfg.get(VERSION_KEY["matplotlib"], ""),
        "numpy_version": cfg.get(VERSION_KEY["numpy"], ""),
        "python_deps_checked_at": cfg.get(TIMESTAMP_KEY, ""),
    }
    if args.json:
        print(json.dumps(summary))
    else:
        print(
            f"PASS  Python deps  "
            f"matplotlib v{summary['matplotlib_version']}, "
            f"numpy v{summary['numpy_version']}  "
            f"({summary['python']})"
        )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001
        print(f"INTERNAL ERROR: {exc}", file=sys.stderr)
        sys.exit(32)
