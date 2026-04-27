"""run_point.py — single-point micrOMEGAs execution.

Runs the micrOMEGAs binary for a single parameter point and writes stdout.log.
Output classification (omega_h2, sigma values, channels, OMEGA_UNCONVERGED)
is performed by the calling agent reading stdout.log per the patterns in
micromegas/SKILL.md §"Reading micrOMEGAs output (agent-driven)".

Public API:
    run(binary: str, work_dir: str, subcommand: str,
        env: dict | None, timeout: int) -> dict
        Returns: {"status", "blocker_code", "stdout_log", "timing_s"}
        status: "success" (returncode 0) or "recoverable" (non-zero / timeout / crash)
        blocker_code: None or "MICROMEGAS_RUNTIME_FAILURE"
        stdout_log: absolute path to the written stdout.log

    run_beps_probe(omega_fine, omega_coarse) -> dict | None
        Returns None if Beps sensitivity OK, or dict with RELIC_BEPS_SENSITIVE info.
"""
import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import json
import math
import os
import subprocess
import time
from pathlib import Path

_SEED = int(os.environ.get("HEPPH_MICROMEGAS_SEED", "42"))


def run(
    binary: str,
    work_dir: str,
    subcommand: str = "relic",
    env: dict | None = None,
    timeout: int = 300,
) -> dict:
    """Execute a micrOMEGAs binary and return status + stdout log path.

    Args:
        binary:     Path to compiled micrOMEGAs main binary.
        work_dir:   Working directory for stdout/stderr logs.
        subcommand: "relic", "scatter", "annihilate", or "indirect".
        env:        Extra env vars (merged with os.environ).
        timeout:    Execution timeout in seconds.

    Returns:
        Dict with keys: status, blocker_code, stdout_log, timing_s.
        Output values (omega_h2, sigma_*, channels) are extracted by the agent
        from stdout.log per micromegas/SKILL.md §"Reading micrOMEGAs output".
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    full_env["HEPPH_MICROMEGAS_SEED"] = str(_SEED)

    stdout_log = work_dir / "stdout.log"
    t0 = time.monotonic()

    try:
        result = subprocess.run(
            [binary],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            env=full_env,
            timeout=timeout,
        )
        timing_s = time.monotonic() - t0
        stdout_log.write_text(result.stdout)
        (work_dir / "stderr.log").write_text(result.stderr)

        if result.returncode != 0:
            return {
                "status": "recoverable",
                "blocker_code": "MICROMEGAS_RUNTIME_FAILURE",
                "stdout_log": str(stdout_log),
                "timing_s": round(timing_s, 3),
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "recoverable",
            "blocker_code": "MICROMEGAS_RUNTIME_FAILURE",
            "stdout_log": str(stdout_log),
            "timing_s": timeout,
        }
    except Exception:
        return {
            "status": "recoverable",
            "blocker_code": "MICROMEGAS_RUNTIME_FAILURE",
            "stdout_log": str(stdout_log),
            "timing_s": 0.0,
        }

    return {
        "status": "success",
        "blocker_code": None,
        "stdout_log": str(stdout_log),
        "timing_s": round(timing_s, 3),
    }


def run_beps_probe(
    omega_fine: float | None,
    omega_coarse: float | None,
) -> dict | None:
    """Check Beps sensitivity between two Ωh² values.

    Args:
        omega_fine:   Ωh² at Beps=1e-6 (default).
        omega_coarse: Ωh² at Beps=1e-4.

    Returns:
        None if sensitivity is acceptable (|Δ|/Ω <= 20%).
        Dict with blocker info if RELIC_BEPS_SENSITIVE.
    """
    if omega_fine is None or omega_coarse is None:
        return None
    if not (math.isfinite(omega_fine) and math.isfinite(omega_coarse)):
        return None
    if omega_fine <= 0 or omega_coarse <= 0:
        return None

    rel_diff = abs(omega_fine - omega_coarse) / omega_fine
    if rel_diff > 0.20:
        return {
            "blocker_code": "RELIC_BEPS_SENSITIVE",
            "mode": "recoverable",
            "omega_h2_fine": omega_fine,
            "omega_h2_coarse": omega_coarse,
            "rel_diff": rel_diff,
        }
    return None


if __name__ == "__main__":
    print(json.dumps({"module": "run_point", "status": "importable"}))
