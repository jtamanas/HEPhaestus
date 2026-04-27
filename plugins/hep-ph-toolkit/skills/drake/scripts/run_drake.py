"""DRAKE runner for agent-driven relic density calculations.

Handles:
- Detecting DRAKE install by shelling out to drake-install/scripts/install.sh detect
- Blocking with DRAKE_NOT_INSTALLED if DRAKE is not configured
- cd-ing to $DRAKE_PATH/test/ before invoking wolframscript
- Capturing stdout+stderr to a log file
- Returning raw stdout so the calling agent can read it directly

The calling agent is responsible for reading stdout and extracting Omega h^2,
x_f, and any other quantities. See SKILL.md for expected output line shapes.

This is a library module for Claude to compose per-task — not a CLI executable.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Locate drake-install/scripts/install.sh relative to this file.
# Layout: plugins/hep-ph-toolkit/skills/drake/scripts/run_drake.py
#         plugins/hep-ph-toolkit/skills/drake-install/scripts/install.sh
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).parent
_DRAKE_INSTALL_SH = (
    _THIS_DIR.parent.parent / "drake-install" / "scripts" / "install.sh"
)


class DRAKENotInstalledError(RuntimeError):
    """DRAKE is not configured or Wolfram Engine is absent."""


class DRAKERunFailedError(RuntimeError):
    """wolframscript exited non-zero or produced no output."""


# ---------------------------------------------------------------------------
# Install detection via drake-install/scripts/install.sh
# ---------------------------------------------------------------------------

def _detect_install() -> dict[str, Any]:
    """Shell out to install.sh detect and return parsed JSON.

    install.sh contract (from drake-install/SKILL.md):
      - Status JSON (configured / found / missing / activation_required /
        manual_download_required) is emitted on stdout, exit 0.
      - Fatal blockers are emitted on stderr as single-line JSON, exit non-zero.
    We capture both streams; on non-zero exit we surface stderr as the error.

    Returns
    -------
    dict: parsed JSON from stdout (keys include "status", and "path" /
          "version" for "configured").
    """
    install_sh = _DRAKE_INSTALL_SH
    if not install_sh.exists():
        raise DRAKENotInstalledError(
            "DRAKE_NOT_INSTALLED: drake-install/scripts/install.sh not found at "
            f"{install_sh}. The drake-install skill is missing from this environment."
        )

    result = subprocess.run(
        ["bash", str(install_sh), "detect"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        stderr_msg = result.stderr.strip() or f"exit {result.returncode}"
        raise DRAKENotInstalledError(
            f"DRAKE_NOT_INSTALLED: install.sh detect exited {result.returncode}. "
            f"Stderr: {stderr_msg}"
        )

    stdout = result.stdout.strip()
    if not stdout:
        raise DRAKENotInstalledError(
            "DRAKE_NOT_INSTALLED: install.sh detect produced no output."
        )

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise DRAKENotInstalledError(
            f"DRAKE_NOT_INSTALLED: install.sh detect returned non-JSON output: "
            f"{stdout[:200]}"
        ) from exc


def _require_drake() -> tuple[Path, Path]:
    """Return (drake_path, wolframscript_path). Raise DRAKENotInstalledError if absent.

    Delegates detection entirely to install.sh detect — no parallel config-reading.
    """
    status_json = _detect_install()
    status = status_json.get("status", "")

    if status == "configured":
        drake_path = Path(status_json["path"])
        # Resolve wolframscript via config or PATH (mirrors install.sh wolfram_path).
        ws_str = _read_config().get("wolfram_engine_path", "")
        ws_path: Path | None = None
        if ws_str and Path(ws_str).is_file() and os.access(ws_str, os.X_OK):
            ws_path = Path(ws_str)
        else:
            import shutil
            found = shutil.which("wolframscript")
            if found:
                ws_path = Path(found)
        if ws_path is None:
            raise DRAKENotInstalledError(
                "DRAKE_WOLFRAM_ABSENT: wolframscript not found. "
                "Run /install to install Wolfram Engine."
            )
        return drake_path, ws_path

    if status == "found":
        raise DRAKENotInstalledError(
            f"DRAKE_NOT_INSTALLED: DRAKE tree found at "
            f"{status_json.get('path', '?')} but not fully configured. "
            "Run /drake-install use-path <dir> to register it."
        )

    # status == "missing" or unknown
    # Note: activation_required is NOT a valid detect output — the detect
    # subcommand only returns configured / found / missing (see drake-install
    # SKILL.md). activation_required is emitted only by use-path / validate.
    raise DRAKENotInstalledError(
        "DRAKE_NOT_INSTALLED: No DRAKE install found. "
        "Run /drake-install to install DRAKE."
    )


# ---------------------------------------------------------------------------
# Config helpers (used only for wolfram_engine_path resolution above)
# ---------------------------------------------------------------------------

def _config_path() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(xdg) / "hepph" / "config.json"


def _read_config() -> dict[str, Any]:
    p = _config_path()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}
    return {}


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_drake(
    *,
    model: str,
    benchmark: str,
    settings: str,
    log_path: str | Path = "/tmp/drake_run.log",
    timeout_seconds: int = 900,
) -> dict[str, Any]:
    """Invoke DRAKE for a built-in model.

    Parameters
    ----------
    model:
        Model identifier passed as the first positional argument to test.wls.
        For built-in models: "WIMP", "VRES", "SE", "TH", "ScalarSingletDM".
    benchmark:
        Benchmark file name (without extension), e.g. "bm_VRES".
        Resolved relative to $DRAKE_PATH/test/ by DRAKE itself.
    settings:
        Settings file name (without extension), e.g. "settings_VRES".
        Resolved relative to $DRAKE_PATH/test/ by DRAKE itself.
    log_path:
        Where to write combined stdout+stderr. Default: /tmp/drake_run.log.
    timeout_seconds:
        Hard timeout for the wolframscript invocation. Default: 900 s (15 min).

    Returns
    -------
    dict with keys:
        stdout (str): raw DRAKE stdout — the calling agent reads this directly
        model (str): model key passed in
        benchmark (str): benchmark file name passed in
        settings (str): settings file name passed in
        log_path (str): absolute path to the combined stdout+stderr log
        drake_path (str): absolute path to the DRAKE root
        drake_version (str): version string from config (written by drake-install)

    Raises
    ------
    DRAKENotInstalledError
        If drake_path or wolframscript is not configured (detected via install.sh).
    DRAKERunFailedError
        If wolframscript exits non-zero or produces no output.
    """
    drake_path, ws_path = _require_drake()
    test_dir = drake_path / "test"
    log_path = Path(log_path)

    cmd = [str(ws_path), "test.wls", model, benchmark, settings]

    try:
        completed = subprocess.run(
            cmd,
            cwd=str(test_dir),       # DRAKE resolves bm_* and settings_* from here
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        raise DRAKERunFailedError(
            f"DRAKE_RUN_FAILED: wolframscript timed out after {timeout_seconds} s. "
            f"Model: {model}, benchmark: {benchmark}, settings: {settings}."
        )

    combined = completed.stdout + "\n" + completed.stderr
    log_path.write_text(combined)

    if completed.returncode != 0 or not completed.stdout.strip():
        tail = combined[-600:].replace("\n", " ") or f"exit={completed.returncode}"
        raise DRAKERunFailedError(
            f"DRAKE_RUN_FAILED: wolframscript exited {completed.returncode}. "
            f"Tail of log: {tail}. Full log: {log_path}"
        )

    # Read drake_version from config (written by drake-install use-path).
    # If absent, block — do not substitute a fabricated version string.
    drake_version = _read_config().get("drake_version", "")
    if not drake_version:
        raise DRAKENotInstalledError(
            "DRAKE_NOT_INSTALLED: drake_version is not set in config. "
            "Re-run /drake-install use-path <dir> to register DRAKE and write "
            "the version to config."
        )

    return {
        "stdout": completed.stdout,
        "model": model,
        "benchmark": benchmark,
        "settings": settings,
        "log_path": str(log_path),
        "drake_path": str(drake_path),
        "drake_version": drake_version,
    }


# ---------------------------------------------------------------------------
# CLI shim (for debugging — not the primary interface)
# ---------------------------------------------------------------------------

def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Run DRAKE for a single model point (debug shim)."
    )
    parser.add_argument("model", help="Model key, e.g. VRES")
    parser.add_argument("benchmark", help="Benchmark file name, e.g. bm_VRES")
    parser.add_argument("settings", help="Settings file name, e.g. settings_VRES")
    parser.add_argument("--log", default="/tmp/drake_run.log", help="Log file path")
    args = parser.parse_args()

    try:
        result = run_drake(
            model=args.model,
            benchmark=args.benchmark,
            settings=args.settings,
            log_path=args.log,
        )
        # Print metadata only; stdout is in log_path and also in result["stdout"]
        summary = {k: v for k, v in result.items() if k != "stdout"}
        print(json.dumps(summary, indent=2))
    except (DRAKENotInstalledError, DRAKERunFailedError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _main()
