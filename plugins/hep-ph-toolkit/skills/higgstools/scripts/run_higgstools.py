"""
run_higgstools.py — CLI entry for /higgstools skill.

Subcommands:
    run        — per-point HB + HS on a single SLHA or scan directory
    aggregate  — collect per-point result.json files into a sorted CSV

Usage:
    run_higgstools.py run --slha <path> [options]
    run_higgstools.py run --model <name> [options]
    run_higgstools.py run --scan-dir <dir> [options]
    run_higgstools.py aggregate <dir> [--output <csv>] [--workers <n>]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))


def _emit_blocker(code: str, mode: str, message: str, user_instruction: str = "") -> None:
    """Emit a JSON blocker to stderr."""
    blocker = {"code": code, "mode": mode, "message": message}
    if user_instruction:
        blocker["user_instruction"] = user_instruction
    print(json.dumps(blocker), file=sys.stderr)


def _load_config() -> dict:
    """Load hephaestus config.json."""
    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "hephaestus"
    config_file = config_dir / "config.json"
    if not config_file.exists():
        return {}
    try:
        return json.loads(config_file.read_text())
    except Exception:
        return {}


def _load_sm_ref_cache(state_root: str) -> dict | None:
    """Load the SM reference chi2 cache. Returns None if absent."""
    cache_path = Path(state_root) / "cache" / "hs2_chi2_sm_ref.json"
    if not cache_path.exists():
        return None
    try:
        return json.loads(cache_path.read_text())
    except Exception:
        return None


def _run_point(
    slha_file: str,
    config: dict,
    args: argparse.Namespace,
    output_dir: str,
) -> dict:
    """
    Run HB+HS on a single SLHA point. Returns result dict.

    Raises SystemExit on fatal errors.
    """
    from slha_adapter import parse_slha, SlhaMissingBlocksError, SlhaMassBlockMissingError

    # Parse SLHA
    try:
        slha_text = Path(slha_file).read_text()
        slha_data = parse_slha(slha_text, allow_legacy=True)
    except SlhaMissingBlocksError as exc:
        _emit_blocker(exc.code, "fatal", exc.message, exc.user_instruction)
        sys.exit(1)
    except SlhaMassBlockMissingError as exc:
        _emit_blocker(exc.code, "fatal", str(exc))
        sys.exit(1)

    backend = args.backend or config.get("higgstools_backend", "legacy")

    # Unified backend gating
    if backend == "unified" and os.environ.get("HEPPH_HIGGSTOOLS_BACKEND") != "unified":
        _emit_blocker(
            "HIGGSTOOLS_BACKEND_UNAVAILABLE",
            "recoverable",
            "--backend=unified requires HEPPH_HIGGSTOOLS_BACKEND=unified env var",
            "Set HEPPH_HIGGSTOOLS_BACKEND=unified or use --backend=legacy (default).",
        )
        # Fall back to legacy
        backend = "legacy"

    state_root = os.environ.get("HEPPH_STATE_ROOT", str(Path.home() / ".local/share/hephaestus"))

    # Check SM ref cache for HS
    mode = getattr(args, "mode", "both")
    chi2_sm_ref = 0.0
    if mode in ("both", "hs"):
        sm_ref = _load_sm_ref_cache(state_root)
        if sm_ref is None:
            _emit_blocker(
                "HIGGSTOOLS_SM_REF_MISSING",
                "fatal",
                "SM reference chi2 cache not found. Install HiggsSignals first.",
                "Run bash _shared/installs/higgstools/install.sh install to install HiggsSignals and cache the SM reference chi2.",
            )
            sys.exit(1)
        chi2_sm_ref = sm_ref.get("chi2_sm_ref", 0.0)

    from exclusion import compute_hb_allowed, compute_hs_consistent

    hb_result = None
    hs_result = None

    if backend == "legacy":
        from legacy_driver import run_higgsbounds, run_higgssignals, write_outputs, HiggsToolsNumericCrash

        hb_build = config.get("higgsbounds_path", "")
        hs_build = config.get("higgssignals_path", "")
        dataset_version = (
            f"HB-{config.get('higgsbounds_version', '5.10.2')}/"
            f"HS-{config.get('higgssignals_version', '2.6.2')}"
        )

        if mode in ("both", "hb"):
            try:
                hb_result = run_higgsbounds(
                    hb_build,
                    slha_file,
                    slha_data["n_neutral"],
                    slha_data["n_charged"],
                    channels=getattr(args, "channels", "all") or "all",
                )
            except HiggsToolsNumericCrash as exc:
                _emit_blocker(exc.code, exc.mode, exc.message, "")
                # recoverable — continue with hb_result=None

        if mode in ("both", "hs"):
            try:
                dMh_val = getattr(args, "dMh", None)
                dMh = _parse_dMh(dMh_val) if dMh_val else None
                hs_result = run_higgssignals(hs_build, slha_file, dMh=dMh)
            except HiggsToolsNumericCrash as exc:
                _emit_blocker(exc.code, exc.mode, exc.message, "")

        hb_allowed = compute_hb_allowed(hb_result.channels if hb_result else [])
        delta_chi2 = getattr(args, "delta_chi2", 6.18) or 6.18
        hs_consistent = compute_hs_consistent(
            hs_result.chi2_total if hs_result else 0.0,
            chi2_sm_ref,
            delta_chi2,
        )

        return write_outputs(
            output_dir=output_dir,
            hb_result=hb_result,
            hs_result=hs_result,
            hb_allowed=hb_allowed,
            hs_consistent=hs_consistent,
            slha_file=slha_file,
            backend="legacy",
            dataset_version=dataset_version,
        )

    else:
        # Unified backend
        from unified_driver import run_unified, UnifiedBackendUnavailable
        try:
            result = run_unified(
                slha_file=slha_file,
                hbdataset_path=config.get("hbdataset_path", ""),
                hsdataset_path=config.get("hsdataset_path", ""),
                hbdataset_commit=config.get("hbdataset_commit", "unknown"),
                hsdataset_commit=config.get("hsdataset_commit", "unknown"),
                n_neutral=slha_data["n_neutral"],
                n_charged=slha_data["n_charged"],
                dMh=_parse_dMh(getattr(args, "dMh", None)),
                delta_chi2=getattr(args, "delta_chi2", 6.18) or 6.18,
                chi2_sm_ref=chi2_sm_ref,
            )
        except UnifiedBackendUnavailable as exc:
            _emit_blocker(exc.code, exc.mode, exc.message, exc.user_instruction)
            sys.exit(1)

        # Write outputs
        os.makedirs(output_dir, exist_ok=True)
        result_path = Path(output_dir) / "result.json"
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result


def _parse_dMh(val: str | None) -> dict[str, float] | None:
    """Parse --dMh as float or JSON object."""
    if val is None:
        return None
    val = val.strip()
    if val.startswith("{"):
        try:
            return json.loads(val)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON for --dMh: {val}") from exc
    try:
        f = float(val)
        return {"h0": f, "heavy": f}
    except ValueError as exc:
        raise ValueError(f"Invalid --dMh value: {val}") from exc


def cmd_run(args: argparse.Namespace) -> int:
    """Execute the 'run' subcommand."""
    config = _load_config()

    # Resolve SLHA file
    slha_file = getattr(args, "slha", None) or getattr(args, "slha_path", None)
    model = getattr(args, "model", None)
    scan_dir = getattr(args, "scan_dir", None)

    state_root = os.environ.get("HEPPH_STATE_ROOT", str(Path.home() / ".local/share/hephaestus"))

    if scan_dir:
        # Fan out over all SLHA files in scan_dir
        return _run_scan_dir(scan_dir, config, args, state_root)

    if model and not slha_file:
        # Look up model's latest SLHA from config
        models = config.get("models", {})
        model_cfg = models.get(model, {})
        slha_file = model_cfg.get("latest_slha", "")
        if not slha_file:
            _emit_blocker(
                "HIGGSTOOLS_SLHA_MISSING_BLOCKS",
                "fatal",
                f"No latest_slha found for model '{model}' in config.",
                f"Run /spheno-build for model '{model}' first to generate an SLHA file.",
            )
            return 1

    if not slha_file:
        print("ERROR: --slha or --model required", file=sys.stderr)
        return 1

    if not Path(slha_file).exists():
        _emit_blocker(
            "HIGGSTOOLS_SLHA_MISSING_BLOCKS",
            "fatal",
            f"SLHA file not found: {slha_file}",
            "Provide a valid SLHA file path with --slha.",
        )
        return 1

    # Determine output directory
    import datetime
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if model:
        output_dir = str(Path(state_root) / "models" / model / "runs" / ts / "higgstools")
    else:
        output_dir = str(Path(state_root) / "runs" / ts / "higgstools")

    result = _run_point(slha_file, config, args, output_dir)
    print(json.dumps(result, indent=2))
    return 0


def _run_scan_dir(scan_dir: str, config: dict, args: argparse.Namespace, state_root: str) -> int:
    """Fan out run over all SLHA files in scan_dir."""
    import datetime

    scan_path = Path(scan_dir)
    slha_files = sorted(scan_path.glob("**/*.slha")) + sorted(scan_path.glob("**/*.spc"))
    if not slha_files:
        print(f"No SLHA files found in {scan_dir}", file=sys.stderr)
        return 1

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # TODO(v1.1): use workers for multiprocessing.Pool; currently serial
    _ = getattr(args, "workers", None) or os.cpu_count() or 1

    results = []
    for i, slha_file in enumerate(slha_files):
        out_dir = str(Path(state_root) / "scan_runs" / ts / f"point_{i:05d}" / "higgstools")
        try:
            result = _run_point(str(slha_file), config, args, out_dir)
            result["slha_file"] = str(slha_file)
            result["index"] = i
            results.append(result)
        except SystemExit:
            results.append({"index": i, "slha_file": str(slha_file), "status": "error"})

    print(json.dumps(results, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="run_higgstools",
        description="HiggsTools constraint checker — HiggsBounds-5 + HiggsSignals-2",
    )
    sub = parser.add_subparsers(dest="subcommand")

    # ── run subcommand ────────────────────────────────────────────────────────
    run_p = sub.add_parser("run", help="Run HB+HS on a single SLHA point or scan directory")
    run_p.add_argument("--model", default=None, help="Model name (reads config.models[name].latest_slha)")
    run_p.add_argument("--slha", default=None, help="Explicit SLHA file path")
    run_p.add_argument("--scan-dir", default=None, help="Fan out over all SLHAs in directory")
    run_p.add_argument("--dMh", default=None, help="Theoretical mass uncertainty [GeV] or JSON object")
    run_p.add_argument(
        "--mode",
        choices=["both", "hb", "hs"],
        default="both",
        help="Run HB only, HS only, or both (default: both)",
    )
    run_p.add_argument(
        "--backend",
        choices=["legacy", "unified"],
        default=None,  # NOT "unified" — default must be None/legacy; env-var gates unified
        help="Backend selection (default: legacy from config)",
    )
    run_p.add_argument(
        "--channels",
        default="all",
        help="HB channel filter: all, neutral, charged, or CSV of IDs",
    )
    run_p.add_argument(
        "--delta-chi2",
        type=float,
        default=6.18,
        dest="delta_chi2",
        help="Δχ² threshold for hs_consistent (default: 6.18, 2D 95%% CL)",
    )
    run_p.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers for scan-dir mode",
    )

    # ── aggregate subcommand ──────────────────────────────────────────────────
    agg_p = sub.add_parser(
        "aggregate",
        help="Collect per-point result.json files into a sorted CSV",
    )
    agg_p.add_argument("dir", help="Scan directory containing per-point result.json files")
    agg_p.add_argument(
        "--output",
        default="higgstools_index.csv",
        help="Output CSV path (default: higgstools_index.csv)",
    )
    agg_p.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers for parsing result.json files",
    )

    return parser


_AGGREGATE_COLUMNS = (
    "index", "hb_allowed", "hs_consistent", "obsratio_max",
    "chi2_total", "chi2_rates", "chi2_masses", "ndf_rates", "ndf_masses",
    "p_value_rates", "p_value_masses", "backend", "dataset_version", "slha_file",
)


def _load_result_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def cmd_aggregate(args: argparse.Namespace) -> int:
    """Walk <dir> for result.json files, sort by index, write priority-ordered CSV."""
    import csv
    scan_dir = Path(args.dir)
    if not scan_dir.exists():
        print(json.dumps({"error": "scan_dir_not_found", "dir": str(scan_dir)}), file=sys.stderr)
        return 1

    paths = sorted(scan_dir.rglob("result.json"))
    workers = args.workers
    if workers and workers > 1:
        from multiprocessing import Pool
        with Pool(workers) as pool:
            rows = pool.map(_load_result_json, paths)
    else:
        rows = [_load_result_json(p) for p in paths]

    rows = [r for r in rows if r]
    rows.sort(key=lambda r: r.get("index", 0))

    out_path = Path(args.output)
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_AGGREGATE_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in _AGGREGATE_COLUMNS})

    print(json.dumps({"output": str(out_path), "rows": len(rows)}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.subcommand == "run":
        return cmd_run(args)
    if args.subcommand == "aggregate":
        return cmd_aggregate(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
