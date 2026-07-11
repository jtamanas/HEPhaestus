#!/usr/bin/env python3
"""
run_looptools.py — CLI entrypoint for /looptools eval.

One-loop direct-detection amplitude evaluation: takes FormCalc's analytically
reduced amplitude (amp_reduced.m + amp_reduced.meta.json), substitutes a
numerical model point, numerically evaluates the Passarino–Veltman integrals via
LoopTools (delegated to a Wolfram/LoopTools MathLink driver), matches onto the
nucleon σ_SI/σ_SD, and emits a scattering/v1 JSON that /ddcalc consumes.

This skill reimplements NO physics: PV evaluation → LoopTools; amplitude →
FormCalc; the only owned logic is parameter-point substitution, the minimal
amplitude→σ transport (match_nucleon.py), and JSON emission + schema validation.

Steps:
  1. Parse args + read config
  2. Validate inputs (amp_reduced.m + meta) — LOOPTOOLS_INPUT_MISSING
  3. Meta compatibility (pv_heads == formcalc-native) — LOOPTOOLS_META_INCOMPATIBLE
  4. Tool gates (skipped in test/stub mode) — WOLFRAM_KERNEL_ABSENT,
     LOOPTOOLS_NOT_CONFIGURED, LOOPTOOLS_MATHLINK_UNAVAILABLE
  5. Cache key + cache-hit check
  6. Prepare numeric model point
  7. Dispatch run_eval.wls (or load the stubbed eval output)
  8. Parse + finiteness-gate the driver output — LOOPTOOLS_AMPLITUDE_NONFINITE
  9. Match to nucleon σ; assemble + validate scattering/v1 — LOOPTOOLS_SCHEMA_INVALID
 10. Write scattering.json + run/<ts>/summary.json + .build_key (atomic, last)

No `reference_only` state and no analytic fallback — per manager rule.  A missing
install or unavailable MathLink is a hard blocker, never a silent approximation.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent.parent.parent
SHARED_HELPERS = REPO_ROOT / "plugins" / "shared" / "install-helpers"

# Make this skill's own scripts/ importable as bare module names, both when run
# as a script (script dir is auto-added) and in-process from tests.  Sibling
# skills ship identically-named modules (cache_key); the tests' conftest clears
# stale sys.modules entries so the looptools copies win.
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

FORM_FACTOR_PRESETS = {"default_2018", "A1"}


# ── Config helpers ─────────────────────────────────────────────────────────────

def _config_path() -> Path:
    cfg_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return Path(cfg_home) / "hephaestus" / "config.json"


def read_config() -> dict:
    p = _config_path()
    if p.exists():
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def emit_blocker(code: str, mode: str, message: str, context: dict | None = None,
                 user_instruction: str | None = None):
    """Emit a single-line blocker JSON on stderr per _shared/blocker.schema.json.

    Only the schema-allowed keys (code, mode, message, context, user_instruction)
    are emitted.
    """
    obj: dict = {"code": code, "mode": mode, "message": message}
    if context is not None:
        obj["context"] = context
    if user_instruction is not None:
        obj["user_instruction"] = user_instruction
    print(json.dumps(obj), file=sys.stderr)


# ── Argument parsing ───────────────────────────────────────────────────────────

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="run_looptools.py",
        description="One-loop direct-detection amplitude evaluation — /looptools eval",
    )
    sub = p.add_subparsers(dest="subcmd")
    ev = sub.add_parser("eval", help="Evaluate amp_reduced.m → scattering/v1")
    ev.add_argument("--amp-reduced", required=True, help="Path to amp_reduced.m")
    ev.add_argument("--point", required=True, help="Path to SLHA / param_card model point")
    ev.add_argument("--output-dir", default="looptools_output", help="Output directory")
    ev.add_argument(
        "--form-factors",
        choices=sorted(FORM_FACTOR_PRESETS),
        default="default_2018",
        dest="form_factors",
        help="Nucleon form-factor preset",
    )
    ev.add_argument("--dm-pdg", type=int, default=None, help="Override DM PDG id")
    ev.add_argument("--force", action="store_true", help="Ignore cache and rerun")
    ev.add_argument(
        "--eval-output",
        default=None,
        help="[TEST-ONLY] Load a pre-baked driver-output JSON instead of dispatching "
             "wolframscript. For the test suite only — bypasses the real "
             "Wolfram/LoopTools evaluation and stamps sigma_provisional. Also "
             "activated via env HEPPH_LOOPTOOLS_TEST_EVAL_OUTPUT. Do NOT use in "
             "production runs.",
    )
    args = p.parse_args(argv)
    if args.subcmd is None:
        p.print_help()
        sys.exit(1)
    return args


# ── Input + meta gates ─────────────────────────────────────────────────────────

def check_inputs(amp_reduced_path: Path, meta_path: Path, point_path: Path):
    """Validate that the FormCalc output + model point exist."""
    missing = [str(x) for x in (amp_reduced_path, meta_path, point_path) if not x.exists()]
    if missing:
        emit_blocker(
            "LOOPTOOLS_INPUT_MISSING",
            "fatal",
            "Required input(s) absent: amp_reduced.m / amp_reduced.meta.json / model point.",
            context={"missing": missing},
            user_instruction="Run /formcalc reduce to produce amp_reduced.m + sidecar, "
                             "and supply a model point (SLHA/param_card) via --point.",
        )
        sys.exit(1)


def check_meta_compat(meta_path: Path, config: dict) -> dict:
    """Read amp_reduced.meta.json and gate on pv_heads + looptools_version skew."""
    with open(meta_path) as f:
        meta = json.load(f)
    pv_heads = meta.get("pv_heads", "")
    if pv_heads != "formcalc-native":
        emit_blocker(
            "LOOPTOOLS_META_INCOMPATIBLE",
            "fatal",
            f"amp_reduced.meta.json pv_heads is {pv_heads!r}, expected 'formcalc-native'.",
            context={"found": pv_heads, "expected": "formcalc-native"},
            user_instruction="Re-run /formcalc reduce (it emits FormCalc-native PV heads).",
        )
        sys.exit(1)
    # looptools_version skew (warn-only here; the config pin is advisory).
    return meta


def tool_gates(config: dict) -> dict:
    """Wolfram + LoopTools + MathLink availability gates (mechanism A).

    Returns a dict of resolved tool paths/versions on success; emits a fatal
    blocker and exits otherwise.
    """
    wolfram_bin = config.get("wolfram_engine_path", "") or ""
    if not wolfram_bin or not Path(wolfram_bin).exists():
        wolfram_bin = subprocess.run(
            ["which", "wolframscript"], capture_output=True, text=True
        ).stdout.strip()
    if not wolfram_bin or not Path(wolfram_bin).exists():
        emit_blocker(
            "WOLFRAM_KERNEL_ABSENT",
            "fatal",
            "wolframscript not found; mechanism A needs a Wolfram kernel.",
            user_instruction="Activate Wolfram Engine (wolframscript --activate).",
        )
        sys.exit(1)

    lt_path = config.get("looptools_path", "") or ""
    if not lt_path or not Path(lt_path).exists():
        emit_blocker(
            "LOOPTOOLS_NOT_CONFIGURED",
            "fatal",
            "config.looptools_path unset or invalid after preflight.",
            context={"path": lt_path},
            user_instruction="Run _shared/installs/looptools (detect.sh / INSTALL.md).",
        )
        sys.exit(1)

    mathlink = str(config.get("looptools_mathlink_available", "")).lower()
    if mathlink != "true":
        emit_blocker(
            "LOOPTOOLS_MATHLINK_UNAVAILABLE",
            "fatal",
            "looptools_mathlink_available != 'true'; mechanism A requires the "
            "LoopTools MathLink binary ($PREFIX/bin/LoopTools).",
            context={"looptools_mathlink_available": mathlink},
            user_instruction="Rebuild LoopTools with Mathematica present so the "
                             "MathLink executable is produced (_shared/installs/looptools).",
        )
        sys.exit(1)

    return {
        "wolfram_bin": wolfram_bin,
        "looptools_path": lt_path,
        "looptools_version": config.get("looptools_version", "2.16"),
    }


# ── Cache ──────────────────────────────────────────────────────────────────────

def _read_build_key(output_dir: Path) -> str:
    bk = output_dir / ".build_key"
    return bk.read_text().strip() if bk.exists() else ""


def cache_hit(output_dir: Path, cache_key: str) -> bool:
    required = [
        output_dir / "scattering.json",
        output_dir / ".build_key",
    ]
    if not all(f.exists() for f in required):
        return False
    return _read_build_key(output_dir) == cache_key


# ── Driver dispatch ────────────────────────────────────────────────────────────

class EvalNoOutput(RuntimeError):
    """run_eval.wls yielded no usable eval_output.json (missing / empty / invalid).

    The defining loud-failure of the eval leg: the Wolfram/LoopTools driver can
    exit 0 (or abort mid-run via MathLink::MLException / libc++abi) yet leave
    eval_output.json absent, empty, or non-JSON — which previously surfaced as a
    raw Python JSONDecodeError traceback.  Carries a classified ``cause`` and, for
    the model-mismatch case, the ``unbound`` amplitude symbols named by the driver.
    """

    def __init__(self, message: str, *, cause: str, log_tail: str,
                 returncode: int, unbound: list[str] | None = None):
        super().__init__(message)
        self.cause = cause
        self.log_tail = log_tail
        self.returncode = returncode
        self.unbound = unbound or []


def _diagnose_eval_failure(driver_log: str, returncode: int) -> str:
    """Classify why the eval produced no output, by scanning the driver log.

    Returns a short cause tag for the LOOPTOOLS_EVAL_NO_OUTPUT blocker context.
    The dominant real-world cause (STEP2.md subtask 3a) is a model mismatch: the
    2HDM+a-specialised run_eval.wls leaves a different model's symbols unbound
    ($Failed / Missing), LoopTools then receives non-numeric args and the MathLink
    aborts (libc++abi) with an empty output.
    """
    log = driver_log or ""
    # Most specific first — the self-test / install messages themselves mention
    # $Failed, so the generic "$Failed ⇒ unbound" heuristic must come last.
    if "UNBOUND-MODEL-PARAMETERS" in log:
        return "unbound_model_parameters"
    if "LoopTools C0i self-test failed" in log:
        return "looptools_selftest_failed"
    if "Install[LoopTools] failed" in log or "LoopTools MathLink binary not found" in log:
        return "looptools_install_failed"
    if "could not read point.json" in log:
        return "point_unreadable"
    if "Get[amp_reduced.m] failed" in log:
        return "amp_unreadable"
    if any(m in log for m in ("MathLink::MLException", "MLException", "libc++abi")):
        return "mathlink_aborted"
    if "$Failed" in log or "Missing[" in log:
        return "unbound_model_parameters"
    return "unknown"


def _extract_unbound(driver_log: str) -> list[str]:
    """Pull the unbound-symbol names out of the driver's UNBOUND-MODEL-PARAMETERS
    marker line (``... {"sym1", "sym2"}``).  Empty list when the marker is absent."""
    if not driver_log:
        return []
    m = re.search(r"UNBOUND-MODEL-PARAMETERS\s*\{([^}]*)\}", driver_log)
    if not m:
        return []
    # Each symbol is a double-quoted string in the driver's InputForm list; the
    # names themselves contain commas (e.g. "ZAMIX(ZAMIX:i,j)"), so extract the
    # quoted tokens rather than splitting on commas.
    return re.findall(r'"([^"]*)"', m.group(1))


def run_driver(
    wolfram_bin: str,
    amp_reduced_path: Path,
    point: dict,
    form_factor_preset: str,
    output_dir: Path,
    run_dir: Path,
    looptools_path: str,
) -> dict:
    """Dispatch run_eval.wls and return the parsed driver output dict.

    Writes point.json into run_dir for the driver to read, invokes wolframscript,
    and reads run_dir/eval_output.json.

    Loud-failure contract (STEP2.md subtask 3a): the driver can exit 0 while
    leaving eval_output.json missing/empty, and an aborted eval can write garbage.
    A missing / empty / non-JSON output is therefore a structured EvalNoOutput
    (never a raw JSONDecodeError), with the cause scanned from the driver log and,
    for the model-mismatch case, the unbound amplitude symbols named.  A genuine
    nonzero exit that still produced a valid output raises RuntimeError.
    """
    driver_script = str(SCRIPT_DIR / "run_eval.wls")
    point_path = run_dir / "point.json"
    point_path.write_text(json.dumps(point, indent=2))
    eval_out_path = run_dir / "eval_output.json"

    args = [
        wolfram_bin, "-script", str(driver_script),
        str(amp_reduced_path),
        str(point_path),
        form_factor_preset,
        str(eval_out_path),
        looptools_path,
    ]
    result = subprocess.run(args, capture_output=True, text=True, timeout=3600)
    driver_log = "\n".join(p for p in (result.stdout or "", result.stderr or "") if p)

    # Require the expected artifact.  Missing OR empty ⇒ the eval did not produce
    # a result, whatever the exit code (the observed defect: exit 0 + empty file).
    if not eval_out_path.exists() or eval_out_path.stat().st_size == 0:
        raise EvalNoOutput(
            "run_eval.wls produced no usable eval_output.json "
            f"({'missing' if not eval_out_path.exists() else 'empty'}); the eval did not run.",
            cause=_diagnose_eval_failure(driver_log, result.returncode),
            log_tail=driver_log[-2000:],
            returncode=result.returncode,
            unbound=_extract_unbound(driver_log),
        )

    # A nonzero exit that nonetheless wrote a file is an infra failure, not a
    # no-output; surface it as a driver failure with the log.
    if result.returncode != 0:
        raise RuntimeError(
            f"run_eval.wls exited {result.returncode}: {result.stderr[-2000:]}"
        )

    # Parse; a non-JSON body (aborted/garbage write) is a no-output, not a
    # raw JSONDecodeError traceback.
    try:
        return json.loads(eval_out_path.read_text())
    except json.JSONDecodeError as exc:
        raise EvalNoOutput(
            f"eval_output.json is not valid JSON ({exc}); the eval aborted mid-write.",
            cause=_diagnose_eval_failure(driver_log, result.returncode),
            log_tail=driver_log[-2000:],
            returncode=result.returncode,
            unbound=_extract_unbound(driver_log),
        ) from None


# ── Main ───────────────────────────────────────────────────────────────────────

def main(argv=None):
    args = parse_args(argv)
    config = read_config()

    amp_reduced_path = Path(args.amp_reduced).resolve()
    meta_path = amp_reduced_path.parent / "amp_reduced.meta.json"
    point_path = Path(args.point).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # TEST-ONLY seam: a pre-baked driver output bypasses wolframscript + tool gates.
    # Gated behind a clearly test-named env var so it is not a production footgun.
    eval_output_override = args.eval_output or os.environ.get("HEPPH_LOOPTOOLS_TEST_EVAL_OUTPUT")
    stub_mode = bool(eval_output_override)

    # Step 2 — input gate.
    check_inputs(amp_reduced_path, meta_path, point_path)

    # Step 3 — meta compatibility.
    check_meta_compat(meta_path, config)

    # Step 4 — tool gates (skipped in stub mode).
    tools = None
    if not stub_mode:
        tools = tool_gates(config)

    # Step 6 — prepare point (before cache key — it feeds the key).
    from prepare_point import prepare_point, DM_PDG_2HDMA
    dm_pdg = args.dm_pdg if args.dm_pdg is not None else DM_PDG_2HDMA
    try:
        point = prepare_point(point_path, dm_pdg=dm_pdg)
    except ValueError as exc:
        emit_blocker(
            "LOOPTOOLS_INPUT_MISSING", "fatal",
            f"Could not read model point: {exc}",
            context={"point": str(point_path)},
        )
        sys.exit(1)

    lt_version = (tools or {}).get("looptools_version", config.get("looptools_version", "2.16"))
    wolfram_version = config.get("wolfram_version", "0.0")

    # Step 5 — cache key + hit.
    from cache_key import compute as compute_cache_key
    key = compute_cache_key(
        amp_reduced_path=amp_reduced_path,
        point=point,
        form_factor_preset=args.form_factors,
        looptools_version=lt_version,
        wolfram_version=wolfram_version,
    )
    if not args.force and cache_hit(output_dir, key):
        print(json.dumps({"status": "ok", "cached": True, "output_dir": str(output_dir)}))
        return 0

    # Step 7 — dispatch driver (or load stub).
    ts = time.strftime("%Y%m%dT%H%M%S")
    run_dir = output_dir / "run" / ts
    run_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    if stub_mode:
        raw = json.loads(Path(eval_output_override).read_text())
    else:
        try:
            raw = run_driver(
                wolfram_bin=tools["wolfram_bin"],
                amp_reduced_path=amp_reduced_path,
                point=point,
                form_factor_preset=args.form_factors,
                output_dir=output_dir,
                run_dir=run_dir,
                looptools_path=tools["looptools_path"],
            )
        except EvalNoOutput as exc:
            # Loud-failure: the eval leg produced no usable output.  Name the
            # cause from the driver log; for a model mismatch (the singlet-doublet
            # symptom) surface the unbound amplitude symbols so step-3 work starts
            # from a guided error, not a crash.
            ctx = {
                "point_id": point.get("dm_pdg"),
                "cause": exc.cause,
                "returncode": exc.returncode,
                "log_tail": exc.log_tail,
            }
            if exc.unbound:
                ctx["unbound_symbols"] = exc.unbound
            if exc.cause == "unbound_model_parameters":
                instruction = (
                    "run_eval.wls is specialised to the 2HDM+a (TwoHdmAfix) model "
                    "and cannot bind this model's amplitude symbols "
                    f"({', '.join(exc.unbound) if exc.unbound else 'see log_tail'}). "
                    "Generalising the substitution/projection/matching layer off "
                    "TwoHdmAfix is roadmap step 3 (LOOP-FLOOR-ROADMAP.md)."
                )
            else:
                instruction = (
                    "Inspect context.log_tail and run/<ts>/ for the driver failure; "
                    "a MathLink abort or LoopTools self-test failure leaves the "
                    "eval output empty."
                )
            emit_blocker(
                "LOOPTOOLS_EVAL_NO_OUTPUT", "recoverable",
                f"run_eval.wls produced no usable eval_output.json (cause: {exc.cause}).",
                context=ctx,
                user_instruction=instruction,
            )
            sys.exit(1)
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            emit_blocker(
                "LOOPTOOLS_DRIVER_FAILED", "fatal",
                f"run_eval.wls failed: {exc}",
                context={"point_id": point.get("dm_pdg")},
            )
            sys.exit(1)
    wall_clock = time.time() - t0

    # Step 8 — parse + finiteness gate.
    from parse_eval_output import parse as parse_eval, AmplitudeNonFinite
    try:
        evd = parse_eval(raw)
    except AmplitudeNonFinite as exc:
        emit_blocker(
            "LOOPTOOLS_AMPLITUDE_NONFINITE", "recoverable",
            f"Evaluated amplitude is non-finite / UV-non-cancelled: {exc}",
            context={"point_id": raw.get("point_id")},
        )
        sys.exit(2)
    except ValueError as exc:
        emit_blocker(
            "LOOPTOOLS_DRIVER_FAILED", "fatal",
            f"Malformed driver output: {exc}",
        )
        sys.exit(1)

    # Step 9 — match to nucleon σ + assemble + validate scattering/v1.
    from match_nucleon import match
    couplings = evd["effective_couplings"]
    sigmas = match(
        m_dm_gev=evd["m_dm_gev"],
        f_p_si_gev_minus2=couplings["f_p_si_gev_minus2"],
        f_n_si_gev_minus2=couplings["f_n_si_gev_minus2"],
        f_p_sd_gev_minus2=couplings.get("f_p_sd_gev_minus2"),
        f_n_sd_gev_minus2=couplings.get("f_n_sd_gev_minus2"),
    )

    from emit_scattering import build, validate, write
    source_run = str(run_dir)
    doc = build(
        m_dm_gev=evd["m_dm_gev"],
        sigmas=sigmas,
        source_run=source_run,
        form_factor_preset=args.form_factors,
        extra={
            "model_source": "hand_crafted_sarah_model",
            "model_fixture": "plugins/hep-ph-toolkit/skills/2hdm-a/fixtures/sarah_model/",
            "loop_topologies": evd.get("loop_topologies", ["chargedHiggs_W_box"]),
            "sigma_provisional": True,
        },
    )
    errors = validate(doc)
    if errors:
        emit_blocker(
            "LOOPTOOLS_SCHEMA_INVALID", "fatal",
            "Emitted scattering/v1 failed schema validation.",
            context={"errors": errors[:5]},
        )
        sys.exit(1)

    scattering_path = output_dir / "scattering.json"
    write(scattering_path, doc)

    # Step 10 — run receipt + .build_key (atomic, last).
    summary = {
        "n_diagrams": evd.get("n_diagrams"),
        "wall_clock_s": round(wall_clock, 3),
        "cached": False,
        "looptools_version": lt_version,
        "n_pv_calls": evd.get("n_pv_calls"),
        "point_id": evd.get("point_id"),
        "stub_mode": stub_mode,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    _write_build_key(output_dir, key)

    print(json.dumps({
        "status": "ok",
        "cached": False,
        "output_dir": str(output_dir),
        "scattering": str(scattering_path),
        "wall_clock_s": round(wall_clock, 3),
    }))
    return 0


def _write_build_key(output_dir: Path, cache_key: str) -> None:
    """Write .build_key via the Phase-0 atomic_write helper when available."""
    dest = output_dir / ".build_key"
    atomic_write_sh = SHARED_HELPERS / "atomic_write.sh"
    common_sh = SHARED_HELPERS / "_common.sh"
    if atomic_write_sh.exists() and common_sh.exists():
        import tempfile
        script = (
            "#!/usr/bin/env bash\n"
            f". {common_sh!s}\n"
            f". {atomic_write_sh!s}\n"
            f"atomic_write_stdin {dest!s}\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as sf:
            sf.write(script)
            sf_path = sf.name
        try:
            result = subprocess.run(
                ["bash", sf_path], input=cache_key + "\n", text=True, capture_output=True
            )
        finally:
            os.unlink(sf_path)
        if result.returncode == 0:
            return
    # Fallback: direct write (still correct, just not fsync-atomic).
    dest.write_text(cache_key + "\n")


if __name__ == "__main__":
    sys.exit(main())
