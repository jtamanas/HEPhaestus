"""run_micromegas.py — CLI entry point for /micromegas skill.

Usage:
    run_micromegas.py <subcommand> <model> [options]

Subcommands:
    relic       <model> [--dm-pdg <id>] [--auto-detect] [--spec <yaml>]
                        [--slha <path>] [--precompiled <project>]
    scatter     <model> [...]
    annihilate  <model> [...]
    indirect    <model> [...]

Exit codes:
    0 — success
    2 — fatal blocker (JSON on stderr)
    3 — recoverable (scan continues, JSON on stderr)

Options:
    --dm-pdg <id>          PDG id of DM candidate (overridden by spec.yaml)
    --auto-detect          Auto-detect DM candidate from SLHA + UFO
    --spec <yaml>          Path to spec.yaml (default: config model spec)
    --slha <path>          Path to SLHA spectrum file
    --precompiled <proj>   Use pre-compiled micrOMEGAs project (MSSM, singletDM, etc.)
    --output-dir <dir>     Output directory (default: $STATE_ROOT/models/<model>/micromegas_runs/<TS>/)
    --scan <NAME=start:stop:step=s>  Scan axis (repeatable, enables scan mode)
"""
import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import argparse
import datetime
import importlib.util
import json
import os
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_EXIT_FATAL = 2
_EXIT_RECOVERABLE = 3

VALID_SUBCOMMANDS = ("relic", "scatter", "annihilate", "indirect")
PRECOMPILED_PROJECTS = ("MSSM", "NMSSM", "singletDM", "IDM")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _emit_blocker(code: str, mode: str, message: str, context: dict | None = None):
    b = {"code": code, "mode": mode, "message": message}
    if context:
        b["context"] = context
    print(json.dumps(b, separators=(",", ":")), file=sys.stderr)


def _load_config() -> dict:
    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "hephaestus"
    config_file = config_dir / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            return json.load(f)
    return {}


def _resolve_run_dir(model: str, state_root: Path) -> Path:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    return state_root / "models" / model / "micromegas_runs" / ts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_micromegas.py",
        description="Run micrOMEGAs for DM calculations.",
    )
    parser.add_argument("subcommand", choices=VALID_SUBCOMMANDS)
    parser.add_argument("model", help="Model name")
    parser.add_argument("--dm-pdg", type=int, default=None)
    parser.add_argument("--auto-detect", action="store_true")
    parser.add_argument("--spec", type=Path, default=None)
    parser.add_argument("--slha", type=Path, default=None)
    parser.add_argument("--precompiled", choices=PRECOMPILED_PROJECTS, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--scan", action="append", default=[], metavar="NAME=start:stop:step=s")

    args = parser.parse_args(argv)
    subcommand = args.subcommand
    model = args.model

    config = _load_config()
    state_root = Path(os.environ.get("HEPPH_STATE_ROOT",
                                      Path.home() / ".local" / "share" / "hephaestus"))

    # ── Check prerequisites ────────────────────────────────────────────────────
    micromegas_path = config.get("micromegas_path", "")
    if not micromegas_path:
        _emit_blocker(
            "MICROMEGAS_INPUT_MISSING", "fatal",
            "micromegas_path not configured. Run _shared/installs/micromegas first.",
            {"missing": "micromegas_path"},
        )
        return _EXIT_FATAL

    # ── Load spec.yaml ────────────────────────────────────────────────────────
    spec_dict = None
    spec_path = args.spec
    if spec_path is None:
        # Try model config
        model_spec = config.get("models", {}).get(model, {}).get("spec_yaml")
        if model_spec:
            spec_path = Path(model_spec)

    if spec_path and spec_path.exists():
        try:
            import yaml
            with open(spec_path) as f:
                spec_dict = yaml.safe_load(f)
        except ImportError:
            try:
                # Fallback: parse YAML manually (basic)
                import re
                spec_dict = {}
            except Exception:
                pass
        except Exception as e:
            _emit_blocker("MICROMEGAS_INPUT_MISSING", "fatal",
                          f"Failed to load spec.yaml: {e}")
            return _EXIT_FATAL

    # ── Resolve DM candidate ──────────────────────────────────────────────────
    resolve_mod = _load_module("resolve_dm_candidate", _SCRIPT_DIR / "resolve_dm_candidate.py")
    slha_mod = _load_module("parse_slha_mass_block", _SCRIPT_DIR / "parse_slha_mass_block.py")

    slha_path = args.slha
    if slha_path is None:
        latest_slha = config.get("models", {}).get(model, {}).get("latest_slha")
        if latest_slha:
            slha_path = Path(latest_slha)

    slha_masses = {}
    if slha_path and slha_path.exists():
        try:
            slha_masses = slha_mod.read_masses(slha_path)
        except Exception:
            pass

    try:
        pdg, dm_name, mass_gev, reason = resolve_mod.resolve(
            spec_dict=spec_dict,
            cli_pdg=args.dm_pdg,
            auto_detect_flag=args.auto_detect,
            slha_masses=slha_masses,
        )
    except resolve_mod.DMResolutionError as e:
        _emit_blocker(e.code, e.mode, str(e))
        return _EXIT_FATAL if e.mode == "fatal" else _EXIT_RECOVERABLE

    dm = {"pdg": pdg, "name": dm_name, "mass_gev": mass_gev}

    # ── Output directory ──────────────────────────────────────────────────────
    run_dir = args.output_dir or _resolve_run_dir(model, state_root)
    run_dir.mkdir(parents=True, exist_ok=True)

    # ── Scan mode vs single-point ─────────────────────────────────────────────
    if args.scan:
        # Scan execution is deferred to v1.1 (MICROMEGAS_SCAN_NOT_IMPLEMENTED).
        # Full grid construction and per-point run_point.run() invocation will
        # be implemented in v1.1 once binary execution is validated end-to-end.
        # See plugins/hep-ph-toolkit/skills/micromegas/scripts/scan.py for the
        # grid-logic library (expand_axis, parse_scan_arg, CSV layout).
        _emit_blocker(
            "MICROMEGAS_SCAN_NOT_IMPLEMENTED",
            "recoverable",
            "The /micromegas --scan subcommand is deferred to v1.1. "
            "Use single-point invocations for now. "
            "Grid logic (expand_axis, parse_scan_arg) is available as a library.",
            {"v1_1_ticket": "connect scan.py to run_point.run() per grid point"},
        )
        return _EXIT_RECOVERABLE

    # ── Single-point run ──────────────────────────────────────────────────────
    # Generate main.c
    template_mod = _load_module("main_c_template", _SCRIPT_DIR / "main_c_template.py")
    main_c = template_mod.render(subcommand, spec_dict, dm)
    (run_dir / "main.c").write_text(main_c)

    # Write summary stub (real run requires actual binary)
    result_data = {
        "status": "queued",
        "subcommand": subcommand,
        "model": model,
        "dm": dm,
        "run_dir": str(run_dir),
        "main_c": str(run_dir / "main.c"),
    }
    print(json.dumps(result_data, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
