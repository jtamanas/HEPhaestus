"""run_class.py — CLI entry point for /class skill.

Usage:
    run_class.py <subcommand> <preset> [options]

Subcommands:
    background  <preset>  Compute background cosmology (H(z), distances, etc.)
    cmb         <preset>  Compute CMB power spectra (TT, TE, EE, BB, PP)
    pk          <preset>  Compute matter power spectrum P(k, z)
    transfer    <preset>  Compute transfer functions T(k, z)

Presets:
    planck18        Planck 2018 ΛCDM best-fit
    planck18_act    Planck 2018 + ACT DR4 joint best-fit
    custom          Requires --config <path>

Options:
    --config <path>      YAML config file (required for custom preset)
    --bsm <path>         YAML BSM extension block
    --output-dir <dir>   Output directory (default: $HEPPH_STATE_ROOT/cosmology_runs/<TS>/)
    --lmax <int>         Maximum multipole for CMB (default: 2500)
    --z-pk <str>         Comma-separated redshifts for pk/transfer (default: "0")
    --k-min <float>      Minimum k [h/Mpc] (default: 1e-4)
    --k-max <float>      Maximum k [h/Mpc] (default: 1.0)

Exit codes:
    0 — success
    2 — fatal blocker (JSON on stderr)
    3 — recoverable (JSON on stderr)
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
_SKILL_DIR = _SCRIPT_DIR.parent
_REPO_ROOT = _SKILL_DIR.parent.parent.parent.parent  # hep-ph-agents/
# m4-fix: sanity-check the repo root so schema lookup failures surface early
# rather than silently producing a wrong path if the file is ever relocated.
assert (_REPO_ROOT / "plugins" / "shared").is_dir(), (
    f"_REPO_ROOT sanity check failed: {_REPO_ROOT!r} does not contain "
    "plugins/shared/. Has run_class.py been moved?"
)

_EXIT_FATAL = 2
_EXIT_RECOVERABLE = 3

VALID_SUBCOMMANDS = ("background", "cmb", "pk", "transfer")
VALID_PRESETS = ("planck18", "planck18_act", "custom")

BSM_KINDS = (
    "dcdm",
    "idm_baryon",
    "idm_dr",
    "idm_photon",
    "exotic_injection",
    "ncdm_extra",
)


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


def _resolve_run_dir(state_root: Path) -> Path:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    return state_root / "cosmology_runs" / ts


def _schema_path() -> Path:
    """Return the absolute path to cosmology.schema.json (shared schemas)."""
    return _REPO_ROOT / "plugins" / "shared" / "schemas" / "cosmology.schema.json"


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser (importable for tests)."""
    parser = argparse.ArgumentParser(
        prog="run_class.py",
        description="Drive CLASS v3.3.4 for linear cosmology calculations.",
    )
    parser.add_argument("subcommand", choices=VALID_SUBCOMMANDS)
    parser.add_argument("preset", choices=VALID_PRESETS)
    parser.add_argument("--config", type=Path, default=None,
                        help="YAML config file (required for preset=custom)")
    parser.add_argument("--bsm", type=Path, default=None,
                        help="YAML BSM extension block")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Output directory (default: $HEPPH_STATE_ROOT/cosmology_runs/<TS>/)")
    parser.add_argument("--lmax", type=int, default=2500,
                        help="Maximum multipole for CMB (default: 2500)")
    parser.add_argument("--z-pk", default="0",
                        help="Comma-separated redshifts for pk/transfer (default: '0')")
    parser.add_argument("--k-min", type=float, default=1e-4,
                        help="Minimum k [h/Mpc] (default: 1e-4)")
    parser.add_argument("--k-max", type=float, default=1.0,
                        help="Maximum k [h/Mpc] (default: 1.0)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    subcommand = args.subcommand
    preset = args.preset

    # ── Validate custom preset requires --config ─────────────────────────────
    if preset == "custom" and args.config is None:
        _emit_blocker(
            "CLASS_CONFIG_INVALID", "fatal",
            "preset=custom requires --config <path>",
            {"missing": "--config"},
        )
        return _EXIT_FATAL

    # ── Load hephaestus config ────────────────────────────────────────────────
    config = _load_config()

    # ── Check class_path is configured ───────────────────────────────────────
    class_path = config.get("class_path", "")
    if not class_path:
        _emit_blocker(
            "CLASS_NOT_CONFIGURED", "fatal",
            "class_path not configured. Run _shared/installs/class first "
            "(bash plugins/hep-ph-toolkit/_shared/installs/class/detect.sh).",
            {"missing": "class_path"},
        )
        return _EXIT_FATAL

    class_version = config.get("class_version", "unknown")
    class_python = config.get("python", sys.executable)

    # ── Resolve output directory ──────────────────────────────────────────────
    state_root = Path(os.environ.get(
        "HEPPH_STATE_ROOT", Path.home() / ".local" / "share" / "hephaestus"
    ))
    run_dir = args.output_dir or _resolve_run_dir(state_root)
    run_dir.mkdir(parents=True, exist_ok=True)

    # ── Load modules ──────────────────────────────────────────────────────────
    ini_render_mod = _load_module("ini_render", _SCRIPT_DIR / "ini_render.py")
    classy_driver_mod = _load_module("classy_driver", _SCRIPT_DIR / "classy_driver.py")
    parse_outputs_mod = _load_module("parse_outputs", _SCRIPT_DIR / "parse_outputs.py")
    schema_validate_mod = _load_module("schema_validate", _SCRIPT_DIR / "schema_validate.py")

    # ── Load BSM extension ────────────────────────────────────────────────────
    bsm_extension = None
    if args.bsm is not None:
        try:
            import yaml  # type: ignore[import]
            with open(args.bsm) as f:
                bsm_extension = yaml.safe_load(f)
        except Exception as exc:
            _emit_blocker(
                "CLASS_CONFIG_INVALID", "fatal",
                f"Failed to load BSM extension file: {exc}",
                {"path": str(args.bsm)},
            )
            return _EXIT_FATAL

        if bsm_extension is not None:
            kind = bsm_extension.get("kind")
            if kind not in BSM_KINDS:
                _emit_blocker(
                    "CLASS_BSM_UNKNOWN_KIND", "fatal",
                    f"Unrecognised BSM extension kind: {kind!r}. "
                    f"Supported: {BSM_KINDS}",
                    {"kind": kind},
                )
                return _EXIT_FATAL

    # ── Render CLASS ini file ─────────────────────────────────────────────────
    try:
        ini_text = ini_render_mod.render(
            subcommand=subcommand,
            preset=preset,
            config_path=args.config,
            bsm_extension=bsm_extension,
            lmax=args.lmax,
            z_pk=args.z_pk,
            k_min=args.k_min,
            k_max=args.k_max,
            templates_dir=_SKILL_DIR / "templates",
        )
    except Exception as exc:
        _emit_blocker(
            "CLASS_INI_RENDER_FAILED", "fatal",
            f"Failed to render CLASS ini file: {exc}",
        )
        return _EXIT_FATAL

    ini_path = run_dir / "class.ini"
    ini_path.write_text(ini_text)

    # ── Run classy ────────────────────────────────────────────────────────────
    try:
        result = classy_driver_mod.run(
            ini_path=ini_path,
            run_dir=run_dir,
            subcommand=subcommand,
            python_exe=class_python,
            lmax=args.lmax,
            z_pk=args.z_pk,
            k_min=args.k_min,
            k_max=args.k_max,
        )
    except classy_driver_mod.ClassSubprocessError as exc:
        # M1-fix: surface specific subprocess error codes (CLASSY_IMPORT_FAILED,
        # CLASS_COMPUTE_FAILED) as distinguishable recoverable blockers so the
        # user knows whether to re-run install or inspect their CLASS ini params.
        _emit_blocker(
            exc.code, "recoverable",
            f"classy subprocess reported: {exc.detail}",
            {"run_dir": str(run_dir)},
        )
        return _EXIT_RECOVERABLE
    except classy_driver_mod.ClassRuntimeError as exc:
        _emit_blocker(
            "CLASS_RUNTIME_FAILURE", "recoverable",
            f"classy subprocess failed: {exc}",
            {"run_dir": str(run_dir)},
        )
        return _EXIT_RECOVERABLE

    # ── Parse outputs to TSV ──────────────────────────────────────────────────
    try:
        output_files = parse_outputs_mod.write_outputs(
            classy_result=result,
            run_dir=run_dir,
            subcommand=subcommand,
        )
    except Exception as exc:
        _emit_blocker(
            "CLASS_OUTPUT_MISSING", "fatal",
            f"Failed to parse/write CLASS outputs: {exc}",
            {"run_dir": str(run_dir)},
        )
        return _EXIT_FATAL

    # ── Build and write cosmology.json ────────────────────────────────────────
    source_run = run_dir.name
    cosmology_doc = {
        "schema_version": "cosmology/v1",
        "cosmology_preset": preset,
        "outputs": [subcommand],
        "class_version": class_version,
        "source_run": source_run,
        "bsm_extension": bsm_extension,
        "results": {
            subcommand: {
                "output_file": str(output_files.get(subcommand, "")),
            }
        },
    }

    # ── Validate cosmology.json ───────────────────────────────────────────────
    schema_path = _schema_path()
    try:
        schema_validate_mod.validate(cosmology_doc, schema_path)
    except schema_validate_mod.SchemaValidationError as exc:
        _emit_blocker(
            "CLASS_SCHEMA_INVALID", "fatal",
            f"cosmology.json failed schema validation: {exc}",
            {"run_dir": str(run_dir)},
        )
        return _EXIT_FATAL

    cosmology_json_path = run_dir / "cosmology.json"
    with open(cosmology_json_path, "w") as f:
        json.dump(cosmology_doc, f, indent=2)
        f.write("\n")

    # ── Print summary ─────────────────────────────────────────────────────────
    summary = {
        "status": "success",
        "subcommand": subcommand,
        "preset": preset,
        "run_dir": str(run_dir),
        "cosmology_json": str(cosmology_json_path),
        "output_files": {k: str(v) for k, v in output_files.items()},
        "class_version": class_version,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
