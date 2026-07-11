"""
/ddcalc run — top-level CLI entry point.

Usage:
    run_ddcalc.py run --sigma-json <path> [--halo <spec>] [--debug]
    run_ddcalc.py exclude --sigma-json <path> [--cl 0.9]
    run_ddcalc.py scan-summary --scan-index <path>

Exits 0 on success; emits blocker JSON to stderr on fatal errors.
Output JSON written to stdout and to $STATE_ROOT/runs/ddcalc/<TS>/result.json.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from validate_scattering import validate_sigma_json  # noqa: E402
from halo import resolve_halo, default_shm  # noqa: E402
from _parse_driver_stdout import parse_driver_stdout  # noqa: E402

# ── Config helpers ─────────────────────────────────────────────────────────────

def _config_get(key: str) -> str:
    """Read a config key from $XDG_CONFIG_HOME/hephaestus/config.json."""
    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "hephaestus"
    config_file = config_dir / "config.json"
    if not config_file.exists():
        return ""
    try:
        with open(config_file) as f:
            return json.load(f).get(key, "") or ""
    except Exception:
        return ""


def _blocker(code: str, message: str, context: dict | None = None, mode: str = "fatal") -> None:
    print(
        json.dumps({
            "code": code,
            "mode": mode,
            "message": message,
            "context": context or {},
        }),
        file=sys.stderr,
    )


def _state_root() -> Path:
    return Path(os.environ.get("HEPPH_STATE_ROOT", Path.home() / ".local" / "share" / "hephaestus"))


# ── DDCalc data-dir symlink fixer ─────────────────────────────────────────────

def _ensure_ddcalc_data_symlinks(ddcalc_path: str) -> None:
    """
    DDCalc 2.2.0 compiles DDInput.f90 with a hardcoded DATA_DIR pointing to the
    build-time temp directory (e.g. /private/var/folders/.../tmp.XXXX/src/data/).
    Everything that DDCalc loads from a file — experiment data (LZ, DARWIN, ...)
    AND the nuclear structure-function tables (SDFF/, Wbar/) — is opened as
    ``DATA_DIR/<subdir>/<file>`` (see DDInput.f90:261-265, DDNuclear.f90:509-551).
    If that path no longer exists (always the case after the build temp dir is
    cleaned up) the OPEN fails silently and the table is left as all-zeros.

    Consequences:
    - Missing experiment dirs => that experiment's init fails loudly.
    - Missing SDFF/ (and Wbar/) => LoadSDFFFile sets the spin-dependent form
      factor WTilde(9,...) to zero (DDNuclear.f90:542-544), so **every**
      spin-dependent rate silently collapses to zero.  Spin-independent rates
      are unaffected because the Helm form factor is computed analytically
      (CalcF2, no file).  This is exactly the "dead SD channel" bug: SI works,
      SD produces zero signal in every experiment.

    This function:
    1. Reads libDDCalc.a strings to find the compile-time data path.
    2. Creates the directory tree at that path (if needed).
    3. Symlinks each experiment data subdirectory AND each nuclear-data
       subdirectory (SDFF, Wbar) from ddcalc_path into the compile-time path.

    Called once per run; the stat() checks are fast (no-op on re-runs).
    """
    import re
    lib_path = Path(ddcalc_path) / "lib" / "libDDCalc.a"
    if not lib_path.exists():
        return

    try:
        result = subprocess.run(
            ["strings", str(lib_path)],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return
    except Exception:
        return

    # Find the compile-time data directory: a line ending in /data/ or /data
    compile_data_dir: str | None = None
    pattern = re.compile(r"^(/[^ \t\n]+/src/data/?)\s*$")
    for line in result.stdout.splitlines():
        m = pattern.match(line.strip())
        if m:
            compile_data_dir = m.group(1).rstrip("/")
            break

    if not compile_data_dir:
        return  # no compile-time path found (Linux build or path already correct)

    compile_data_path = Path(compile_data_dir)
    ddcalc = Path(ddcalc_path)

    # Find data subdirs in the install tree that DDCalc opens at runtime:
    #   * experiment dirs — any subdir that contains energies.dat
    #   * nuclear structure-function tables — SDFF/ and Wbar/ (no energies.dat,
    #     so they must be named explicitly).  SDFF/ is what makes the SD channel
    #     live; omitting it silently zeroes every spin-dependent rate.
    try:
        exp_dirs = [
            d for d in ddcalc.iterdir()
            if d.is_dir() and (d / "energies.dat").exists()
        ]
    except Exception:
        return

    nuclear_dirs = [
        ddcalc / name for name in ("SDFF", "Wbar")
        if (ddcalc / name).is_dir()
    ]
    data_dirs = exp_dirs + nuclear_dirs

    if not data_dirs:
        return

    # Check if all symlinks already exist and are valid:
    if all(
        (compile_data_path / d.name).is_symlink()
        and (compile_data_path / d.name).exists()
        for d in data_dirs
    ):
        return  # already set up

    # Create directory and symlinks:
    try:
        compile_data_path.mkdir(parents=True, exist_ok=True)
        for d in data_dirs:
            link = compile_data_path / d.name
            if not link.exists() and not link.is_symlink():
                link.symlink_to(d.resolve())
    except Exception:
        pass  # best-effort; if it fails, experiment/SD init will report the error


# ── Driver compilation + caching ───────────────────────────────────────────────

def _ensure_driver(ddcalc_path: str) -> Path:
    """
    Build ddcalc_driver from source, caching by source + lib hash.
    Returns path to compiled binary.
    """
    import hashlib
    driver_src = SCRIPTS_DIR / "ddcalc_driver.c"
    lib_path = Path(ddcalc_path) / "lib" / "libDDCalc.a"

    if not driver_src.exists():
        raise FileNotFoundError(f"ddcalc_driver.c not found: {driver_src}")
    if not lib_path.exists():
        raise FileNotFoundError(f"libDDCalc.a not found: {lib_path}")

    # Cache key: sha256 of (driver source + lib)
    h = hashlib.sha256()
    h.update(driver_src.read_bytes())
    h.update(lib_path.read_bytes()[:4096])  # first 4kB as proxy
    cache_sha = h.hexdigest()[:16]

    cache_dir = _state_root() / "cache" / "ddcalc_driver" / cache_sha
    driver_bin = cache_dir / "driver"

    if driver_bin.exists():
        return driver_bin

    cache_dir.mkdir(parents=True, exist_ok=True)

    # Compile
    include_dir = Path(ddcalc_path) / "include"
    compile_cmd = [
        "gcc", "-std=c11",
        "-Wno-implicit-function-declaration",
        str(driver_src),
        f"-I{include_dir}",
        f"-L{Path(ddcalc_path) / 'lib'}",
        "-lDDCalc", "-lgfortran", "-lm",
        "-o", str(driver_bin),
    ]

    # On macOS (Homebrew gcc/gfortran), the libgfortran is not in the default
    # linker search path.  Ask gfortran where it lives and inject the -L flag.
    try:
        gf_lib_dir_result = subprocess.run(
            ["gfortran", "-print-file-name=libgfortran.a"],
            capture_output=True, text=True,
        )
        if gf_lib_dir_result.returncode == 0:
            gf_lib_path = gf_lib_dir_result.stdout.strip()
            gf_lib_dir = str(Path(gf_lib_path).parent)
            if gf_lib_dir and gf_lib_dir != "libgfortran.a":
                # Insert right before "-lgfortran"
                idx = compile_cmd.index("-lgfortran")
                compile_cmd.insert(idx, f"-L{gf_lib_dir}")
    except Exception:
        pass  # best-effort; let gcc try without the explicit -L

    result = subprocess.run(compile_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Driver compile failed:\n{result.stderr[:2000]}"
        )

    return driver_bin


# ── /ddcalc run ────────────────────────────────────────────────────────────────

def cmd_run(args) -> int:
    sigma_path = args.sigma_json

    # 1. Validate input
    try:
        sigma_doc = validate_sigma_json(sigma_path)
    except Exception as e:
        _blocker("DDCALC_INPUT_INVALID", str(e), {"path": sigma_path})
        return 1

    # 2. Check mass range
    m_dm = sigma_doc["m_dm_gev"]
    if m_dm < 0.1:
        _blocker(
            "DDCALC_MASS_OUT_OF_RANGE",
            f"m_dm_gev={m_dm} is below 0.1 GeV (sub-GeV DM). "
            "Use DarkELF or similar for sub-GeV direct detection.",
            {"m_dm_gev": m_dm, "suggested_tool": "DarkELF"},
            mode="recoverable",
        )
        return 1

    # 3. Resolve halo
    try:
        halo = resolve_halo(sigma_doc)
    except NotImplementedError as e:
        _blocker("DDCALC_INPUT_INVALID", str(e))
        return 1

    # 4. Get DDCalc path
    ddcalc_path = _config_get("ddcalc_path")
    if not ddcalc_path:
        _blocker(
            "DDCALC_DRIVER_FAILED",
            "ddcalc_path not configured. Run _shared/installs/ddcalc first.",
        )
        return 1

    # 5a. Ensure DDCalc data symlinks (needed for experiments with external data files,
    #     e.g. LZ 2022, DARWIN — DDInput.f90 uses a compile-time data dir that
    #     disappears after the build temp tree is removed).
    _ensure_ddcalc_data_symlinks(ddcalc_path)

    # 5b. Ensure driver
    try:
        driver_bin = _ensure_driver(ddcalc_path)
    except Exception as e:
        _blocker("DDCALC_DRIVER_FAILED", f"Driver build failed: {e}")
        return 1

    # 6. Inject halo into sigma doc for driver
    halo_augmented = dict(sigma_doc)
    halo_augmented["v0_km_per_s"] = halo.v0_km_per_s
    halo_augmented["vesc_km_per_s"] = halo.vesc_km_per_s
    halo_augmented["rho0_gev_per_cm3"] = halo.rho0_gev_per_cm3

    # 7. Run driver
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        json.dump(halo_augmented, tf)
        tf_path = tf.name

    try:
        result = subprocess.run(
            [str(driver_bin), tf_path],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        _blocker("DDCALC_DRIVER_FAILED", "DDCalc driver timed out after 120s")
        return 1
    finally:
        Path(tf_path).unlink(missing_ok=True)

    if result.returncode != 0:
        _blocker(
            "DDCALC_DRIVER_FAILED",
            f"DDCalc driver exited {result.returncode}",
            {"stderr_tail": result.stderr[-1000:]},
        )
        return 1

    # 8. Parse output
    try:
        driver_result = parse_driver_stdout(result.stdout)
    except ValueError as e:
        _blocker("DDCALC_DRIVER_FAILED", f"Driver output parse error: {e}")
        return 1

    # 9. Determine overall verdict
    any_excluded = any(
        e.get("excluded_90cl", False)
        for e in driver_result["experiments"].values()
    )
    verdict = "excluded" if any_excluded else "allowed"

    # 10. Build output JSON
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    experiment_set = _config_get("ddcalc_experiment_set") or "native"
    overlay_sha = _config_get("ddcalc_experiment_overlay_sha") or None
    upstream_commit = _config_get("ddcalc_upstream_commit") or "unknown"

    output = {
        "schema_version": "ddcalc_result/v1",
        "status": "ok",
        "verdict": verdict,
        "m_dm_gev": m_dm,
        "experiments": driver_result["experiments"],
        "neutrino_fog": {"source": "ddcalc_builtin_2.2.0"},
        "halo_used": halo.to_dict(),
        "nucleon_form_factors_used": sigma_doc.get("nucleon_form_factors", {}),
        "inputs_echo": {
            "sigma_si_proton_cm2": sigma_doc.get("sigma_si_proton_cm2"),
            "sigma_si_neutron_cm2": sigma_doc.get("sigma_si_neutron_cm2"),
            "sigma_sd_proton_cm2": sigma_doc.get("sigma_sd_proton_cm2"),
            "sigma_sd_neutron_cm2": sigma_doc.get("sigma_sd_neutron_cm2"),
            "source": sigma_doc.get("source"),
        },
        "ddcalc_version": driver_result.get("ddcalc_version", "2.2.0"),
        "ddcalc_upstream_commit": upstream_commit,
        "experiment_set": experiment_set,
        "experiment_overlay_sha": overlay_sha,
    }

    # 11. Write to state root
    run_dir = _state_root() / "runs" / "ddcalc" / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    result_path = run_dir / "result.json"
    result_path.write_text(json.dumps(output, indent=2) + "\n")
    output["report_path"] = str(run_dir / "report.md")

    if args.debug:
        output["driver_stdout"] = result.stdout

    print(json.dumps(output, indent=2))
    return 0


# ── /ddcalc exclude ────────────────────────────────────────────────────────────

def cmd_exclude(args) -> int:
    """Thin wrapper: runs `run` and emits only the verdict + experiment exclusion flags."""
    # Delegate to run
    args.debug = False
    rc = cmd_run(args)
    return rc


# ── /ddcalc scan-summary ───────────────────────────────────────────────────────

def cmd_scan_summary(args) -> int:
    """Read a scan index JSON and call run per point, writing a CSV summary."""
    from scan_summary import run_scan_summary
    return run_scan_summary(args.scan_index)


# ── Argument parser ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="/ddcalc — DDCalc likelihood driver")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Run DDCalc on a single point")
    p_run.add_argument("--sigma-json", required=True, help="Path to scattering/v1 JSON")
    p_run.add_argument("--halo", help="Halo spec (reserved; SHM only in v1)")
    p_run.add_argument("--debug", action="store_true", help="Include driver stdout in output")

    p_excl = sub.add_parser("exclude", help="Emit verdict for a single point")
    p_excl.add_argument("--sigma-json", required=True)
    p_excl.add_argument("--cl", type=float, default=0.9, help="Confidence level (default 0.9)")

    p_scan = sub.add_parser("scan-summary", help="Summarise a scan directory")
    p_scan.add_argument("--scan-index", required=True, help="Path to scan index JSON")

    args = parser.parse_args()

    if args.command == "run":
        sys.exit(cmd_run(args))
    elif args.command == "exclude":
        sys.exit(cmd_exclude(args))
    elif args.command == "scan-summary":
        sys.exit(cmd_scan_summary(args))


if __name__ == "__main__":
    main()
