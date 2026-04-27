"""
scan_summary.py — flock-guarded, serial scan-point summariser.

Reads a scan index JSON (list of {point_idx, sigma_json_path} objects),
calls ddcalc for each point, writes ddcalc_scan.csv.

CSV columns:
    point_idx, m_dm_gev, sigma_si_proton_cm2, verdict, logL_XENON1T_2018,
    logL_LUX_2016, logL_PandaX_2017, logL_PICO_60_2019, logL_DarkSide_50,
    n_sigma_fog

File is written to $STATE_ROOT/models/<model>/ddcalc_runs/<TS>/ddcalc_scan.csv
(or <scan_output_dir>/ddcalc_scan.csv if scan index specifies output_dir).

flock is used around the output directory to prevent concurrent writes
from parallel callers (none in v1, but reserved per spec §3).
"""
from __future__ import annotations

import csv
import fcntl
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from _parse_driver_stdout import parse_driver_stdout  # noqa: E402
from halo import resolve_halo  # noqa: E402
from validate_scattering import validate_sigma_json  # noqa: E402


NATIVE_EXPERIMENTS = [
    "XENON1T_2018",
    "LUX_2016",
    "PandaX_2017",
    "PICO_60_2019",
    "DarkSide_50",
]

CSV_COLUMNS = (
    ["point_idx", "m_dm_gev", "sigma_si_proton_cm2", "verdict"]
    + [f"logL_{exp}" for exp in NATIVE_EXPERIMENTS]
    + ["n_sigma_fog"]
)


def _state_root() -> Path:
    return Path(
        os.environ.get("HEPPH_STATE_ROOT", Path.home() / ".local" / "share" / "hephaestus")
    )


def _config_get(key: str) -> str:
    config_dir = (
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "hephaestus"
    )
    config_file = config_dir / "config.json"
    if not config_file.exists():
        return ""
    try:
        with open(config_file) as f:
            return json.load(f).get(key, "") or ""
    except Exception:
        return ""


def run_single_point(sigma_json_path: str, driver_bin: Path, ddcalc_path: str) -> dict | None:
    """
    Run DDCalc on one scattering JSON. Returns parsed experiment dict or None on error.
    """
    try:
        sigma_doc = validate_sigma_json(sigma_json_path)
    except Exception as e:
        print(f"[scan_summary] Validation error for {sigma_json_path}: {e}", file=sys.stderr)
        return None

    halo = resolve_halo(sigma_doc)
    halo_augmented = dict(sigma_doc)
    halo_augmented["v0_km_per_s"] = halo.v0_km_per_s
    halo_augmented["vesc_km_per_s"] = halo.vesc_km_per_s
    halo_augmented["rho0_gev_per_cm3"] = halo.rho0_gev_per_cm3

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
    finally:
        Path(tf_path).unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"[scan_summary] Driver failed for {sigma_json_path}: {result.stderr[:200]}", file=sys.stderr)
        return None

    try:
        return parse_driver_stdout(result.stdout)
    except ValueError as e:
        print(f"[scan_summary] Parse error for {sigma_json_path}: {e}", file=sys.stderr)
        return None


def run_scan_summary(scan_index_path: str) -> int:
    """
    Main entry point for scan-summary subcommand.
    Returns exit code (0 = success).
    """
    from run_ddcalc import _ensure_driver  # local import to avoid circular

    scan_index_path = Path(scan_index_path)
    if not scan_index_path.exists():
        print(
            json.dumps({
                "code": "DDCALC_INPUT_INVALID",
                "mode": "fatal",
                "message": f"Scan index not found: {scan_index_path}",
                "context": {},
            }),
            file=sys.stderr,
        )
        return 1

    with open(scan_index_path) as f:
        scan_index = json.load(f)

    ddcalc_path = _config_get("ddcalc_path")
    if not ddcalc_path:
        print(
            json.dumps({
                "code": "DDCALC_DRIVER_FAILED",
                "mode": "fatal",
                "message": "ddcalc_path not configured. Run /ddcalc-install first.",
                "context": {},
            }),
            file=sys.stderr,
        )
        return 1

    try:
        driver_bin = _ensure_driver(ddcalc_path)
    except Exception as e:
        print(
            json.dumps({
                "code": "DDCALC_DRIVER_FAILED",
                "mode": "fatal",
                "message": f"Driver build failed: {e}",
                "context": {},
            }),
            file=sys.stderr,
        )
        return 1

    # Determine output directory
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir_str = scan_index[0].get("output_dir", "") if scan_index else ""
    if output_dir_str:
        output_dir = Path(output_dir_str) / "ddcalc_runs" / ts
    else:
        output_dir = _state_root() / "runs" / "ddcalc" / f"scan_{ts}"
    output_dir.mkdir(parents=True, exist_ok=True)

    lock_dir = _state_root() / ".locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / "ddcalc"

    csv_path = output_dir / "ddcalc_scan.csv"

    # Flock around the output write (reserved for v1.1 parallel scans)
    with open(lock_path, "w") as lock_f:
        try:
            fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("[scan_summary] Another scan is running (lock held). Waiting...", file=sys.stderr)
            fcntl.flock(lock_f, fcntl.LOCK_EX)

        rows = []
        for entry in sorted(scan_index, key=lambda e: e.get("point_idx", 0)):
            point_idx = entry.get("point_idx", 0)
            sigma_path = entry.get("sigma_json_path", "")

            result = run_single_point(sigma_path, driver_bin, ddcalc_path)
            if result is None:
                continue

            exps = result.get("experiments", {})
            any_excl = any(e.get("excluded_90cl", False) for e in exps.values())
            verdict = "excluded" if any_excl else "allowed"

            # Load sigma values for CSV
            try:
                doc = validate_sigma_json(sigma_path)
                m_dm = doc.get("m_dm_gev", "")
                sig_si_p = doc.get("sigma_si_proton_cm2", "")
            except Exception:
                m_dm = ""
                sig_si_p = ""

            row: dict = {
                "point_idx": point_idx,
                "m_dm_gev": m_dm,
                "sigma_si_proton_cm2": sig_si_p,
                "verdict": verdict,
                "n_sigma_fog": "",
            }
            for exp_name in NATIVE_EXPERIMENTS:
                exp_data = exps.get(exp_name, {})
                row[f"logL_{exp_name}"] = exp_data.get("logL", "")
            rows.append(row)

        # Write CSV (deterministic: sorted by point_idx, fixed column order)
        rows.sort(key=lambda r: r.get("point_idx", 0))
        with open(csv_path, "w", newline="") as csvf:
            writer = csv.DictWriter(csvf, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

        fcntl.flock(lock_f, fcntl.LOCK_UN)

    print(f"Scan summary written to: {csv_path}")
    return 0
