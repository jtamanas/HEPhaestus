"""
run_spheno.py — CLI entry point for /spheno-build.

Dispatches compile + single-point run or Cartesian scan.

Usage:
    python3 run_spheno.py <model_name> [options]

Options:
    --params k=v,...            Patch MINPAR parameters (comma-separated).
    --input-card <path>         Use an existing LesHouches input card verbatim.
    --scan NAME=start:stop:step=s  Scan axis (repeatable). Implies scan mode.
    --force                     Force recompile even if cache key matches.
    --skip-compile              Skip compile stage (binary must already exist).
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import datetime
import hashlib
import importlib.util as _ilu
import json
import re
import secrets
import shutil
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPT_DIR.parent
_SHARED_DIR = _SKILL_DIR.parent / "_shared"
_CONFIG_HELPERS = _SKILL_DIR.parent.parent.parent / "shared" / "install-helpers" / "config_helpers.py"


def _load_module(name: str, path: Path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _now_ts() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%MZ")


def _overrides_hash(overrides: dict[str, float] | None) -> str:
    """8-char blake2b hex of the override set (JSON-canonical, sorted keys)."""
    payload = json.dumps(overrides or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.blake2b(payload.encode("utf-8"), digest_size=4).hexdigest()


def _unique_run_dir(parent: Path, ts: str, overrides: dict[str, float] | None) -> Path:
    """Return a collision-free run dir path under *parent* for this minute.

    Format: ``<ts>-<8 hex>``. Suffix is a blake2b hash of the override set.
    If a directory with that exact name already exists (identical overrides
    inside the same UTC minute), appends a ``secrets.token_hex(2)`` salt
    until the name is unique. Does not create the directory.
    """
    suffix = _overrides_hash(overrides)
    candidate = parent / f"{ts}-{suffix}"
    while candidate.exists():
        salt = secrets.token_hex(2)
        salted = hashlib.blake2b(
            (suffix + salt).encode("utf-8"), digest_size=4
        ).hexdigest()
        candidate = parent / f"{ts}-{salted}"
    return candidate


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="/spheno-build: compile + run SPheno for a named model."
    )
    parser.add_argument("model_name", help="Model name (e.g. dark_su3)")
    parser.add_argument(
        "--params", default="",
        help="Comma-separated MINPAR overrides: MpsiD=300,gD=1.2"
    )
    parser.add_argument(
        "--input-card", dest="input_card", default=None,
        help="Path to an existing LesHouches input card. Used verbatim; no templating."
    )
    parser.add_argument(
        "--scan", action="append", dest="scan_args", default=[],
        metavar="NAME=start:stop:step=s",
        help="Scan axis (repeatable). Enables scan mode."
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Force recompile even if cache matches."
    )
    parser.add_argument(
        "--skip-compile", action="store_true",
        help="Skip the compile stage (binary must already exist)."
    )
    parser.add_argument(
        "--no-register", action="store_true",
        help="Do NOT move the model's latest_slha convenience pointer to this "
             "run. The per-run SLHA is still written under $STATE_ROOT and its "
             "path is echoed in stdout; only the global latest_slha cache is "
             "left untouched. Use for parameter scans, where every point would "
             "otherwise overwrite the pointer and leave it stuck at whichever "
             "point ran last (poisoning the next latest_slha consumer). The "
             "provenance guard (register_latest_slha) is what --no-register "
             "skips, so pass the per-point slha_path explicitly downstream."
    )
    parser.add_argument(
        "--backend", choices=["spheno", "analytic"], default=None,
        help="Override the spectrum backend for this run. Without this flag "
             "the spec's backends.spectrum (or the analytic fallback) decides. "
             "Use --backend spheno to opt a model into a real SPheno spectrum "
             "with HiggsBounds coupling blocks (e.g. singlet_doublet, whose "
             "default stays analytic)."
    )
    args = parser.parse_args()

    config_helpers = _load_module("config_helpers", _CONFIG_HELPERS)
    config = config_helpers.load_config()
    state_root = config_helpers.STATE_ROOT
    model_dir = state_root / "models" / args.model_name

    # ---------------------------------------------------------------------------
    # Stage 1: Compile (unless --skip-compile)
    # ---------------------------------------------------------------------------
    if not args.skip_compile:
        compile_mod = _load_module("compile_model", _SCRIPT_DIR / "compile_model.py")
        compile_result = compile_mod.compile_model(args.model_name, force=args.force)
        print(json.dumps({"stage": "compile", **compile_result}))
        spheno_bin_path = compile_result.get("binary")
    else:
        sarah_name_mod = _load_module("sarah_name", _SHARED_DIR / "sarah_name.py")
        try:
            sarah_name = sarah_name_mod.modelspec_name_to_sarah(args.model_name)
        except ValueError as e:
            print(json.dumps({"code": "SPHENO_NO_OUTPUT", "mode": "fatal",
                              "message": str(e)}), file=sys.stderr)
            sys.exit(1)
        spheno_bin_path = str(model_dir / "spheno_bin" / f"SPheno{sarah_name}")

    # ---------------------------------------------------------------------------
    # Parse --params
    # ---------------------------------------------------------------------------
    overrides: dict[str, float] = {}
    if args.params.strip():
        for kv in args.params.split(","):
            kv = kv.strip()
            if "=" not in kv:
                print(f"error: --params entry must be NAME=VALUE, got: {kv!r}",
                      file=sys.stderr)
                sys.exit(2)
            k, v = kv.split("=", 1)
            try:
                overrides[k.strip()] = float(v.strip())
            except ValueError:
                print(f"error: invalid float value for {k!r}: {v!r}", file=sys.stderr)
                sys.exit(2)

    # ---------------------------------------------------------------------------
    # Stage 2: Run (scan or single-point)
    # ---------------------------------------------------------------------------
    if args.scan_args:
        # Scan mode
        scan_mod = _load_module("scan", _SCRIPT_DIR / "scan.py")
        axes = []
        for scan_arg in args.scan_args:
            axes.append(scan_mod.parse_scan_arg(scan_arg))

        ts = _now_ts()
        scan_dir = model_dir / "runs" / f"scan_{ts}"
        csv_path = scan_mod.scan(args.model_name, axes, scan_dir)

        print(json.dumps({"stage": "scan", "status": "done",
                          "scan_index_csv": str(csv_path)}))
        return

    # Single-point mode
    ts = _now_ts()
    runs_parent = model_dir / "runs"
    runs_parent.mkdir(parents=True, exist_ok=True)
    run_dir = _unique_run_dir(runs_parent, ts, overrides)
    run_dir.mkdir(parents=True, exist_ok=False)
    run_tag = run_dir.name

    if args.input_card:
        # Verbatim copy: no templating
        src = Path(args.input_card)
        if not src.exists():
            print(f"error: --input-card file not found: {src}", file=sys.stderr)
            sys.exit(1)
        lh_in = run_dir / "LesHouches.in"
        shutil.copy2(str(src), str(lh_in))
        spec = {}  # no spec loaded in --input-card mode
    else:
        # Template from spec
        lht_mod = _load_module("leshouches_template", _SCRIPT_DIR / "leshouches_template.py")
        spec_path = model_dir / "spec.yaml"
        if not spec_path.exists():
            print(
                json.dumps({
                    "code": "SPHENO_NO_OUTPUT",
                    "mode": "fatal",
                    "message": f"spec.yaml not found at {spec_path}. Run /sarah-build first.",
                }),
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            import yaml
            with open(spec_path) as f:
                spec = yaml.safe_load(f)
        except ImportError:
            print("error: pyyaml required", file=sys.stderr)
            sys.exit(1)

        # Loud guard: a user --params override that names a parameter with no
        # MINPAR/BSMPARAMS les_houches index would be silently dropped from the
        # card (the value would never reach SPheno). Refuse rather than run a
        # point that does not mean what the user asked for.
        if overrides:
            placeable = lht_mod.input_scalar_params(spec)
            stray = sorted(set(overrides) - set(placeable))
            if stray:
                print(
                    json.dumps({
                        "code": "SPHENO_BAD_OVERRIDE",
                        "mode": "fatal",
                        "message": (
                            f"--params override(s) {stray} name parameters with "
                            "no les_houches:[BSMPARAMS/MINPAR, N] index; they "
                            "would not reach the LesHouches card. Valid inputs: "
                            f"{sorted(placeable)}."
                        ),
                    }),
                    file=sys.stderr,
                )
                sys.exit(1)

        card_text = lht_mod.build(spec, overrides=overrides)

        # Append SPHENOINPUT block if available
        sarah_name_mod = _load_module("sarah_name", _SHARED_DIR / "sarah_name.py")
        try:
            sarah_name = sarah_name_mod.modelspec_name_to_sarah(args.model_name)
        except ValueError:
            sarah_name = args.model_name

        from scan import _extract_sphenoinput_block  # noqa: PLC0415
        sphenoinput_file = (
            model_dir / "sarah_output" / "SPheno" / sarah_name /
            "Input_Files" / f"LesHouches.in.{sarah_name}"
        )
        if sphenoinput_file.exists():
            block = _extract_sphenoinput_block(sphenoinput_file.read_text())
            if block:
                # Disable ONLY the SPheno passes that genuinely NaN/hang for
                # the singlet-doublet rank-1 Dirac sub-block: 3-body decays
                # (``13`` → "negative mass squared", stop) and the low-energy
                # constraints pass (``57`` → hangs in ``CalculateBR``). These
                # live in the 3-body / U-factor loop-decay machinery, which is
                # NOT on the path that produces the effective Higgs-coupling
                # blocks HiggsTools needs.
                #
                # Flags ``11`` (branching ratios) and ``16`` (one-loop decays)
                # are LEFT ENABLED (SARAH default = 1): the diagnosis proved
                # 11=1,16=1,13=0,57=0 runs clean and emits
                # HiggsCouplingsFermions/HiggsCouplingsBosons + EFFHIGGSCOUPLINGS
                # with FChi1/2/3 = 132.69/523.03/540.33 and zero NaN. The
                # earlier belief that ``16`` itself NaNs was a red herring —
                # the crash is reached only down the 13/57 decay path.
                # See sarah-workarounds.md §16.
                for flag_num, flag_label in [
                    ("13", "3-Body decays"),
                    ("57", "Calculate low energy"),
                ]:
                    block = re.sub(
                        rf"^(\s*{flag_num}\s+)\S+(\s+#\s*{re.escape(flag_label)}.*)$",
                        r"\g<1>0\g<2>",
                        block,
                        flags=re.MULTILINE,
                    )
                card_text = card_text.rstrip() + "\n\n" + block + "\n"

        lh_in = run_dir / "LesHouches.in"
        lh_in.write_text(card_text)

    # Dispatch to the selected spectrum backend (spheno or analytic).
    # An explicit --backend overrides the spec's backends.spectrum for this run
    # only (in-memory), so a model whose spec defaults to analytic — e.g.
    # singlet_doublet — can opt into a real SPheno spectrum without editing the
    # spec on disk. Injected into the local spec dict the dispatcher reads.
    if args.backend and 'spec' in locals() and isinstance(spec, dict):
        spec.setdefault("backends", {})["spectrum"] = args.backend
    dispatcher_mod = _load_module("dispatcher", _SCRIPT_DIR / "dispatcher.py")
    params_for_dispatch: dict[str, float] = {}
    if 'spec' in locals():
        for p in spec.get("parameters", []):
            params_for_dispatch[p["name"]] = float(p.get("default", 0.0))
    params_for_dispatch.update(overrides)

    result = dispatcher_mod.dispatch(
        model_name=args.model_name,
        spec=spec if 'spec' in locals() else {},
        params=params_for_dispatch,
        out_dir=run_dir,
        config=config,
    )
    result["run_dir"] = str(run_dir)
    result["stage"] = "run"
    print(json.dumps(result))

    # Update config on success.
    #
    # --no-register skips this entirely: the per-run SLHA still exists on disk
    # (its path is in `result["slha_path"]`, printed above), but the global
    # latest_slha convenience pointer is NOT moved. This keeps a scan from
    # rewriting the pointer once per point and leaving it stuck at the last
    # point run. When should the pointer move? On a single canonical-point run
    # you want downstream DD consumers to pick up automatically. When should it
    # NOT? During a scan, where "latest" is ambiguous — pass the per-point
    # slha_path explicitly to each DD run instead of trusting latest_slha.
    if args.no_register:
        if result.get("status") in ("ok", "recoverable"):
            print(json.dumps({"stage": "register", "status": "skipped",
                              "reason": "--no-register",
                              "slha_path": result.get("slha_path")}))
    elif result.get("status") in ("ok", "recoverable"):
        slha_path = result.get("slha_path")
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if slha_path:
            # Record latest_slha WITH provenance (content fingerprint + the
            # parameter point/params it was produced for) so a later stale
            # pointer is detectable. latest_slha is only a convenience cache.
            config_helpers.register_latest_slha(
                args.model_name,
                slha_path,
                point=run_tag,
                params=params_for_dispatch,
                spheno_bin=spheno_bin_path,
                latest_run=run_tag,
                spheno_built_at=now,
            )
        else:
            config_helpers.register_model(
                args.model_name,
                spheno_bin=spheno_bin_path,
                latest_run=run_tag,
                spheno_built_at=now,
            )


if __name__ == "__main__":
    main()
