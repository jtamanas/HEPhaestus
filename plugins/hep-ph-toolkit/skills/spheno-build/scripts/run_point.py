"""
run_point.py — Stage 2 of /spheno-build: single SPheno invocation + classification.

Usage (library):
    from run_point import run
    result = run("dark_su3", input_card=Path("LesHouches.in"), out_dir=Path("runs/ts"))

The SPheno binary is invoked with two positional arguments (spec §5):
    <spheno_bin>  <out_dir>/LesHouches.in  <out_dir>/SPheno.spc
No shell redirection.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import json
import shutil
import subprocess
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPT_DIR.parent
_SHARED_DIR = _SKILL_DIR.parent / "_shared"
_CONFIG_HELPERS = _SKILL_DIR.parent.parent.parent / "shared" / "install-helpers" / "config_helpers.py"

import importlib.util as _ilu


def _load_config_helpers():
    if _CONFIG_HELPERS.exists():
        spec = _ilu.spec_from_file_location("config_helpers", _CONFIG_HELPERS)
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    raise ImportError(f"config_helpers.py not found at {_CONFIG_HELPERS}")


def _load_sarah_name():
    candidate = _SHARED_DIR / "sarah_name.py"
    if not candidate.exists():
        raise ImportError(f"sarah_name.py not found at {candidate}")
    spec = _ilu.spec_from_file_location("sarah_name", candidate)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_parse_slha():
    candidate = _SCRIPT_DIR / "parse_slha.py"
    spec = _ilu.spec_from_file_location("parse_slha", candidate)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _emit_blocker(code: str, mode: str, message: str, context: dict | None = None) -> None:
    blocker: dict = {"code": code, "mode": mode, "message": message}
    if context:
        blocker["context"] = context
    print(json.dumps(blocker), file=sys.stderr)


def run(
    model_name: str,
    input_card: Path,
    out_dir: Path,
) -> dict:
    """Run SPheno for a single parameter point.

    Copies input_card to out_dir/LesHouches.in, then invokes:
        <spheno_bin>  <out_dir>/LesHouches.in  <out_dir>/SPheno.spc

    Returns a classification dict:
        {
          "status": "ok" | "recoverable" | "fatal",
          "blocker_code": str | None,
          "slha_path": str | None,
          "summary": dict | None,
        }
    On fatal errors, also emits a blocker JSON to stderr.
    Does NOT call sys.exit — callers (scan.py) decide how to handle fatal rows.
    """
    config_helpers = _load_config_helpers()
    sarah_name_mod = _load_sarah_name()
    parse_slha_mod = _load_parse_slha()

    config = config_helpers.load_config()

    try:
        sarah_name = sarah_name_mod.modelspec_name_to_sarah(model_name)
    except ValueError as e:
        _emit_blocker("SPHENO_NO_OUTPUT", "fatal", f"Invalid model name: {e}")
        return {"status": "fatal", "blocker_code": "SPHENO_NO_OUTPUT", "slha_path": None, "summary": None}

    state_root = config_helpers.STATE_ROOT
    model_dir = state_root / "models" / model_name
    spheno_bin = model_dir / "spheno_bin" / f"SPheno{sarah_name}"

    if not spheno_bin.exists():
        msg = f"SPheno binary not found at {spheno_bin}. Run compile stage first."
        _emit_blocker("SPHENO_NO_OUTPUT", "fatal", msg, {"binary_path": str(spheno_bin)})
        return {"status": "fatal", "blocker_code": "SPHENO_NO_OUTPUT", "slha_path": None, "summary": None}

    out_dir.mkdir(parents=True, exist_ok=True)

    # Copy input card into run dir. The SPheno backend already stages
    # the LesHouches.in *into* ``out_dir`` before calling us, so the
    # source and destination paths may resolve to the same file —
    # ``shutil.copy2`` raises ``SameFileError`` in that case. Detect and
    # skip when the card is already in place.
    lh_in = out_dir / "LesHouches.in"
    if Path(input_card).resolve() != lh_in.resolve():
        shutil.copy2(str(input_card), str(lh_in))

    spc_out = out_dir / "SPheno.spc"

    # Invoke SPheno: two positional args (spec §5).
    # cwd=out_dir so SPheno's auxiliary outputs (BR_*.dat, *_GammaTot.dat,
    # effC.dat, …) land in the per-run dir instead of the caller's cwd.
    # Inputs are passed as absolute paths so they still resolve after the
    # cwd change (in case lh_in / spc_out were constructed from a relative
    # out_dir).
    abs_lh_in = Path(lh_in).resolve()
    abs_spc_out = Path(spc_out).resolve()
    abs_out_dir = Path(out_dir).resolve()
    cmd = [str(spheno_bin), str(abs_lh_in), str(abs_spc_out)]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=600,
            cwd=str(abs_out_dir),
        )
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        exit_code = -1
        proc = None

    # Check for output file
    if exit_code != 0 or not spc_out.exists():
        msg = (
            f"SPheno exited with code {exit_code} or produced no output at {spc_out}."
        )
        ctx: dict = {"exit_code": exit_code, "spc_path": str(spc_out)}
        if proc and proc.stdout:
            ctx["stdout_tail"] = "\n".join(proc.stdout.splitlines()[-20:])
        _emit_blocker("SPHENO_NO_OUTPUT", "fatal", msg, ctx)
        return {"status": "fatal", "blocker_code": "SPHENO_NO_OUTPUT", "slha_path": None, "summary": None}

    # Parse SLHA output
    try:
        summary = parse_slha_mod.parse(spc_out)
    except Exception as e:
        msg = f"SLHA parse failed: {e}"
        _emit_blocker("SPHENO_NO_OUTPUT", "fatal", msg)
        return {"status": "fatal", "blocker_code": "SPHENO_NO_OUTPUT", "slha_path": str(spc_out), "summary": None}

    # Write summary.json
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    # Classify result
    problems = summary.get("problems", [])
    spinfo_warnings = summary.get("spinfo_warnings", [])

    if set(problems) & {1, 2, 3}:
        blocker_code = "SPHENO_SPECTRUM_PROBLEM"
        _emit_blocker(
            blocker_code, "recoverable",
            f"SPheno Block PROBLEM contains code(s) {problems}. Spectrum unphysical.",
            {"problems": problems},
        )
        return {
            "status": "recoverable",
            "blocker_code": blocker_code,
            "slha_path": str(spc_out),
            "summary": summary,
        }

    if spinfo_warnings:
        blocker_code = "SPHENO_RGE_NONCONVERGENT"
        _emit_blocker(
            blocker_code, "recoverable",
            f"SPheno Block SPINFO item 4 present: {spinfo_warnings[0]!r}.",
            {"spinfo_warnings": spinfo_warnings},
        )
        return {
            "status": "recoverable",
            "blocker_code": blocker_code,
            "slha_path": str(spc_out),
            "summary": summary,
        }

    if not summary.get("masses"):
        msg = "SPheno.spc present but Block MASS is empty."
        _emit_blocker("SPHENO_NO_OUTPUT", "fatal", msg)
        return {"status": "fatal", "blocker_code": "SPHENO_NO_OUTPUT", "slha_path": str(spc_out), "summary": summary}

    return {
        "status": "ok",
        "blocker_code": None,
        "slha_path": str(spc_out),
        "summary": summary,
    }
