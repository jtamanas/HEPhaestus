"""classy_driver.py — subprocess wrapper around classy.

Runs classy in a child process so that segfaults or crashes do not
kill the agent. Captures stdout/stderr to log files. Returns a dict
with the computed observables keyed by subcommand.

No NumPy, SciPy, or SymPy — this module orchestrates classy only.
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path


class ClassRuntimeError(Exception):
    """Raised when the classy subprocess exits non-zero."""


class ClassSubprocessError(ClassRuntimeError):
    """Raised when the classy subprocess emits a structured error code.

    Attributes
    ----------
    code : str
        The specific error code emitted by the subprocess
        (e.g. ``CLASSY_IMPORT_FAILED``, ``CLASS_COMPUTE_FAILED``).
    detail : str
        Human-readable detail from the subprocess.
    """

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


# ---------------------------------------------------------------------------
# Public runner
# ---------------------------------------------------------------------------

def run(
    *,
    ini_path: Path,
    run_dir: Path,
    subcommand: str,
    python_exe: str,
    lmax: int,
    z_pk: str,
    k_min: float,
    k_max: float,
) -> dict:
    """Run classy in a subprocess and return parsed result dict.

    Parameters
    ----------
    ini_path:
        Path to the rendered CLASS ini file.
    run_dir:
        Directory where stdout.log/stderr.log will be written.
    subcommand:
        One of background|cmb|pk|transfer — controls which output dict
        keys the embedded Python script extracts.
    python_exe:
        Python interpreter that has classy installed.
    lmax, z_pk, k_min, k_max:
        Resolution controls mirrored to the classy call for output extraction.

    Returns
    -------
    dict
        Parsed result dict with subcommand-specific keys (e.g. 'cls', 'pk', etc.)
    """
    script = _build_classy_script(
        ini_path=ini_path,
        subcommand=subcommand,
        lmax=lmax,
        z_pk=z_pk,
        k_min=k_min,
        k_max=k_max,
    )

    stdout_log = run_dir / "stdout.log"
    stderr_log = run_dir / "stderr.log"

    try:
        proc = subprocess.run(
            [python_exe, "-c", script],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired as exc:
        raise ClassRuntimeError(
            f"classy subprocess timed out after 300 s: {exc}"
        ) from exc
    except Exception as exc:
        raise ClassRuntimeError(f"Failed to launch classy subprocess: {exc}") from exc

    stdout_log.write_text(proc.stdout)
    stderr_log.write_text(proc.stderr)

    if proc.returncode != 0:
        # M1-fix: before raising a generic ClassRuntimeError, try to parse the
        # subprocess stdout as JSON — the embedded script emits a structured
        # {"error": "<CODE>", "detail": "..."} on CLASSY_IMPORT_FAILED and
        # CLASS_COMPUTE_FAILED so the caller can surface the specific code.
        stdout_stripped = proc.stdout.strip()
        if stdout_stripped:
            try:
                error_payload = json.loads(stdout_stripped)
                if "error" in error_payload:
                    raise ClassSubprocessError(
                        error_payload["error"],
                        error_payload.get("detail", ""),
                    )
            except json.JSONDecodeError:
                pass  # Fall through to generic error below

        stderr_tail = proc.stderr[-500:] if proc.stderr else "(empty)"
        raise ClassRuntimeError(
            f"classy exited with code {proc.returncode}. "
            f"stderr tail: {stderr_tail!r}"
        )

    # Parse JSON output from the successful embedded script run
    try:
        result = json.loads(proc.stdout.strip())
    except json.JSONDecodeError as exc:
        raise ClassRuntimeError(
            f"classy script produced non-JSON stdout. "
            f"stdout: {proc.stdout[:300]!r}. "
            f"Error: {exc}"
        ) from exc

    return result


# ---------------------------------------------------------------------------
# Embedded Python script builder
# ---------------------------------------------------------------------------

def _build_classy_script(
    *,
    ini_path: Path,
    subcommand: str,
    lmax: int,
    z_pk: str,
    k_min: float,
    k_max: float,
) -> str:
    """Build the Python source string that runs classy and emits JSON."""
    # z_pk as a list of floats for use in classy calls
    z_pk_repr = repr([float(z) for z in z_pk.split(",") if z.strip()])

    script = textwrap.dedent(f"""
        import sys, json, pathlib

        try:
            from classy import Class
        except ImportError as exc:
            print(json.dumps({{"error": "CLASSY_IMPORT_FAILED", "detail": str(exc)}}))
            sys.exit(1)

        ini_path = pathlib.Path({str(ini_path)!r})

        # Parse ini file into a dict for Class.set()
        params = {{}}
        for line in ini_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                params[k.strip()] = v.strip()

        c = Class()
        c.set(params)

        try:
            c.compute()
        except Exception as exc:
            c.struct_cleanup()
            c.empty()
            print(json.dumps({{"error": "CLASS_COMPUTE_FAILED", "detail": str(exc)}}))
            sys.exit(1)

        result = {{"subcommand": {subcommand!r}}}

        if {subcommand!r} == "background":
            bg = c.get_background()
            # bg is a dict of numpy arrays; convert to lists of strings
            result["background"] = {{k: [f"{{x:.10e}}" for x in arr.tolist()]
                                      for k, arr in bg.items()}}
            result["age_gyr"] = f"{{c.age():.10e}}"

        elif {subcommand!r} == "cmb":
            cls = c.lensed_cl({lmax!r})
            result["cls"] = {{k: [f"{{x:.10e}}" for x in arr.tolist()]
                               for k, arr in cls.items()}}
            result["lmax"] = {lmax!r}

        elif {subcommand!r} == "pk":
            # B2-fix: grid is in h/Mpc; convert to 1/Mpc before pk_lin(),
            # then divide P by h^3 so output is in (Mpc/h)^3 = (h/Mpc)^-3.
            # Header k_h/Mpc is therefore honest.
            z_list = {z_pk_repr}
            k_min = {k_min!r}
            k_max = {k_max!r}
            h = c.h()
            n_k = 200
            # k grid in h/Mpc (as advertised in header)
            k_h_values = [k_min * (k_max / k_min) ** (i / (n_k - 1)) for i in range(n_k)]
            pk_by_z = {{}}
            for z in z_list:
                # pk_lin() takes k in 1/Mpc; returns P in Mpc^3
                # Convert output to (Mpc/h)^3 by dividing by h^3
                pk_by_z[str(z)] = [
                    f"{{c.pk_lin(k * h, z) / h**3:.10e}}" for k in k_h_values
                ]
            result["k_h"] = [f"{{k:.10e}}" for k in k_h_values]
            result["pk_by_z"] = pk_by_z
            result["z_list"] = [str(z) for z in z_list]

        elif {subcommand!r} == "transfer":
            # B1-fix: use c.get_transfer(z) which returns the real transfer
            # functions T(k,z) per species (d_cdm, d_b, d_g, d_ur, d_tot, ...).
            # The k-grid from get_transfer is already in h/Mpc.
            z_list = {z_pk_repr}
            # Components to extract (always present in CLASS output)
            _TK_COMPONENTS = ("d_cdm", "d_b", "d_tot")
            tk_by_z = {{}}
            k_h_ref = None
            for z in z_list:
                tk_dict = c.get_transfer(z)
                # k (h/Mpc) is the k-grid key in classy's get_transfer output
                k_arr = tk_dict["k (h/Mpc)"].tolist()
                if k_h_ref is None:
                    k_h_ref = k_arr
                components = {{}}
                for comp in _TK_COMPONENTS:
                    if comp in tk_dict:
                        components[comp] = [f"{{v:.10e}}" for v in tk_dict[comp].tolist()]
                tk_by_z[str(z)] = components
            result["k_h"] = [f"{{k:.10e}}" for k in k_h_ref]
            result["tk_by_z"] = tk_by_z
            result["z_list"] = [str(z) for z in z_list]
            result["tk_components"] = _TK_COMPONENTS

        c.struct_cleanup()
        c.empty()

        print(json.dumps(result))
    """)

    return script
