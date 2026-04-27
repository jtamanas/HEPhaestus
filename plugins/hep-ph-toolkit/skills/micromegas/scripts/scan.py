"""scan.py — Sequential Cartesian-product parameter scan for /micromegas.

Imports parse_axis and expand_axis from /spheno-build/scripts/scan.py to
avoid reimplementing grid logic. Columns mirror /spheno-build scan with
micromegas-specific additions.

Usage (library):
    from scan import scan, parse_scan_arg
    csv_path = scan("singletDM", "relic", dm, axes, scan_dir, spec_dict)

Usage (CLI):
    python3 scan.py singletDM relic --scan lhs=50:200:step=50

Scan index CSV columns:
    index, <params>, omega_h2, sigma_si_p, sigma_sd_p, sigma_v_0,
    status, blocker_code, run_dir, timing_s
"""
import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import csv
import importlib.util
import json
import os
from pathlib import Path
import time

_SCRIPT_DIR = Path(__file__).resolve().parent

# Import expand_axis from /spheno-build (shared grid logic).
_SPHENO_SCAN_PATH = (
    _SCRIPT_DIR.parents[3]
    / "hep-ph-toolkit" / "skills" / "spheno-build" / "scripts" / "scan.py"
)


def _load_spheno_scan():
    spec = importlib.util.spec_from_file_location("spheno_scan", _SPHENO_SCAN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def expand_axis(name: str, start: float, stop: float, step: float) -> list[float]:
    """Expand a scan axis. Delegates to spheno-build's expand_axis for consistency."""
    try:
        spheno_mod = _load_spheno_scan()
        return spheno_mod.expand_axis(name, start, stop, step)
    except Exception:
        # Fallback implementation if spheno-build not available
        if step <= 0:
            raise ValueError(f"scan axis {name!r}: step must be positive, got {step}")
        if start > stop:
            raise ValueError(f"scan axis {name!r}: start ({start}) > stop ({stop})")
        values: list[float] = []
        n = 0
        while True:
            v = start + n * step
            if v > stop + step * 0.5:
                break
            if v <= stop + step * 1e-9:
                values.append(round(v, 12))
            n += 1
        return values


def parse_scan_arg(arg: str) -> tuple[str, float, float, float]:
    """Parse --scan argument. Delegates to spheno-build for format compatibility."""
    try:
        spheno_mod = _load_spheno_scan()
        return spheno_mod.parse_scan_arg(arg)
    except Exception:
        import re
        m = re.fullmatch(
            r"([A-Za-z_][A-Za-z0-9_]*)=([^:]+):([^:]+):step=([^:]+)",
            arg.strip(),
        )
        if not m:
            raise ValueError(
                f"Cannot parse --scan argument {arg!r}. "
                "Expected format: NAME=start:stop:step=s"
            )
        return m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4))


def _cartesian_product(axes: list[tuple[str, list[float]]]) -> list[dict[str, float]]:
    """Return the Cartesian product of axes as a list of parameter dicts."""
    if not axes:
        return [{}]
    sorted_axes = sorted(axes, key=lambda a: a[0])

    def _recurse(idx: int, partial: dict) -> list[dict]:
        if idx == len(sorted_axes):
            return [dict(partial)]
        name, values = sorted_axes[idx]
        result = []
        for v in values:
            partial[name] = v
            result.extend(_recurse(idx + 1, partial))
        return result

    return _recurse(0, {})


def scan(
    model: str,
    subcommand: str,
    dm: dict,
    axes: list[tuple[str, float, float, float]],
    scan_dir: Path,
    spec: dict | None = None,
) -> Path:
    """Build scan grid and write scan_index.csv with per-row blockers.

    NOTE (v1.1 TODO): Full scan execution (calling run_point.run() per grid
    point) is deferred to v1.1. Each row is written with
    status='MICROMEGAS_SCAN_NOT_IMPLEMENTED' indicating the grid was built but
    no binary was invoked. The CLI (/micromegas --scan) emits the
    MICROMEGAS_SCAN_NOT_IMPLEMENTED recoverable blocker before reaching this
    function. This function is retained as a library for grid-logic tests
    (expand_axis, parse_scan_arg, _cartesian_product, CSV column layout).

    Args:
        model:      Model name.
        subcommand: "relic", "scatter", "annihilate", "indirect".
        dm:         DM candidate dict.
        axes:       List of (name, start, stop, step) tuples.
        scan_dir:   Directory to write scan outputs.
        spec:       Spec dict.

    Returns:
        Path to the generated scan_index.csv.
    """
    scan_dir = Path(scan_dir)
    scan_dir.mkdir(parents=True, exist_ok=True)

    expanded_axes: list[tuple[str, list[float]]] = []
    for name, start, stop, step in axes:
        values = expand_axis(name, start, stop, step)
        expanded_axes.append((name, values))

    points = _cartesian_product(expanded_axes)
    param_names = sorted(ax[0] for ax in expanded_axes)

    csv_path = scan_dir / "scan_index.csv"
    fieldnames = ["index"] + param_names + [
        "omega_h2", "sigma_si_p", "sigma_sd_p", "sigma_v_0",
        "status", "blocker_code", "run_dir", "timing_s",
    ]

    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for idx, point in enumerate(points):
            point_dir = scan_dir / f"{idx:04d}"
            point_dir.mkdir(parents=True, exist_ok=True)

            t0 = time.monotonic()
            row: dict = {"index": idx}
            row.update({k: point.get(k, "") for k in param_names})

            # v1.1 TODO: call run_point.run(binary, str(point_dir), subcommand)
            # here and populate omega_h2/sigma_* from the result.
            # For now emit a clear per-row blocker so callers are not misled.
            row["omega_h2"] = ""
            row["sigma_si_p"] = ""
            row["sigma_sd_p"] = ""
            row["sigma_v_0"] = ""
            row["status"] = "MICROMEGAS_SCAN_NOT_IMPLEMENTED"
            row["blocker_code"] = "MICROMEGAS_SCAN_NOT_IMPLEMENTED"
            row["run_dir"] = str(point_dir)
            row["timing_s"] = round(time.monotonic() - t0, 3)

            writer.writerow(row)

    return csv_path


if __name__ == "__main__":
    import argparse
    import datetime

    parser = argparse.ArgumentParser(description="micrOMEGAs Cartesian-product scan.")
    parser.add_argument("model_name", help="Model name")
    parser.add_argument("subcommand", choices=("relic", "scatter", "annihilate", "indirect"))
    parser.add_argument("--scan", action="append", required=True, metavar="NAME=start:stop:step=s",
                        dest="scan_args")
    parser.add_argument("--dm-pdg", type=int, default=0)
    parser.add_argument("--dm-name", default="DM")
    parser.add_argument("--dm-mass", type=float, default=0.0)
    args = parser.parse_args()

    dm = {"pdg": args.dm_pdg, "name": args.dm_name, "mass_gev": args.dm_mass}
    state_root = Path(os.environ.get("HEPPH_STATE_ROOT",
                                      Path.home() / ".local" / "share" / "hephaestus"))
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    scan_out_dir = state_root / "models" / args.model_name / "runs" / f"scan_{ts}"

    parsed_axes = []
    for scan_arg in args.scan_args:
        parsed_axes.append(parse_scan_arg(scan_arg))

    csv_out = scan(args.model_name, args.subcommand, dm, parsed_axes, scan_out_dir)
    print(json.dumps({"status": "done", "scan_index_csv": str(csv_out)}))
