#!/usr/bin/env python3
"""
run_formcalc.py — CLI entrypoint for /formcalc reduce.

Steps:
  1. Parse args
  2. Read config (formcalc_path, form_binary, wolfram_engine_path, versions)
  3. Resolve state dir, create input/ symlinks
  4. FeynArts version gate (read FeynAmpList.meta.json)
  5. γ₅ static check (delegate to gamma5_static_check.wls)
  6. Cache key computation + cache hit check
  7. Dispatch to run_calcfeynamp.wls
  8. Parse summary + write sidecar
  9. Write .build_key atomically last
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
# Make sibling helper modules importable whether run_formcalc.py is invoked
# directly (python scripts/run_formcalc.py) or imported as part of a package.
# Mirrors run_feynarts.py, which inserts its scripts dir on sys.path and imports
# the helpers by bare name (from cache_key import ...) rather than
# `from cache_key import ...` (the latter ModuleNotFoundErrors on direct
# invocation because there is no top-level `scripts` package on the path).
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SKILL_DIR = SCRIPT_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent.parent.parent
SCHEMAS_DIR = REPO_ROOT / "plugins" / "shared" / "schemas"
SHARED_HELPERS = REPO_ROOT / "plugins" / "shared" / "install-helpers"

# Phase-0 sidecar schema
AMP_REDUCED_SCHEMA = SCHEMAS_DIR / "amp_reduced.meta.schema.json"

# Supported FeynArts versions for v1
SUPPORTED_FEYNARTS_VERSIONS = {"3.11"}

# Supported gamma5 schemes (accepted by the parser + valid in the sidecar enum).
GAMMA5_SCHEMES = {"naive", "hv", "bmhv", "larin"}

# γ₅ schemes actually wired through to CalcFeynAmp. FormCalc 9.10 computes with
# native anticommuting γ₅ (NDR) and exposes no CalcFeynAmp option that selects a
# complete HV/BMHV/Larin scheme (only Gamma5Test — a consistency *diagnostic* —
# and Gamma5ToEps — an ε-tensor substitution inside *closed fermion traces*
# only, which does not implement a full scheme and is inert on trace-free
# amplitudes). `run_calcfeynamp.wls` therefore forwards no γ₅ option, so every
# reduction is genuine NDR. Accepting hv/bmhv/larin here and stamping the sidecar
# with them would be a validated-looking lie (STEP3-DESIGN.md Decision 1 / R1);
# the refuse-to-lie guard below hard-errors on any non-implemented scheme.
GAMMA5_IMPLEMENTED = {"naive"}

# Supported regulators
REGULATORS = {"dimreg", "cdr", "thv"}


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


def emit_blocker(code: str, mode: str, message: str, **extra):
    obj = {"code": code, "mode": mode, "message": message}
    obj.update(extra)
    print(json.dumps(obj), file=sys.stderr)


# ── γ₅ refuse-to-lie guard ──────────────────────────────────────────────────────

def check_gamma5_implemented(scheme: Optional[str]) -> None:
    """Refuse to run for any γ₅ scheme not genuinely wired to CalcFeynAmp.

    STEP3-DESIGN.md Decision 1 (G1a) / Risk R1: the toolkit historically accepted
    --gamma5 {naive,hv,bmhv,larin} and recorded the value in the cache key and the
    sidecar, but run_calcfeynamp.wls only ever passed FermionChains + Dimension to
    CalcFeynAmp — the scheme was never forwarded, so every reduction was FormCalc's
    native anticommuting-γ₅ (NDR) regardless of the flag. A sidecar stamped "hv"
    was therefore a validated-looking lie.

    Only ``naive`` is honest (== FormCalc 9.10 NDR default). Any other scheme
    hard-errors with FORMCALC_G5_SCHEME_UNIMPLEMENTED (silent-failures-loud norm)
    instead of being silently stamped. ``None`` is allowed here — the separate
    static-check gate (FORMCALC_G5_SCHEME_REQUIRED) decides whether a scheme is
    mandatory for a given amplitude, and the sidecar records the effective naive.
    """
    if scheme is None or scheme in GAMMA5_IMPLEMENTED:
        return
    emit_blocker(
        "FORMCALC_G5_SCHEME_UNIMPLEMENTED",
        "fatal",
        f"γ₅ scheme '{scheme}' is not implemented: it is not forwarded to "
        "CalcFeynAmp, so requesting it would silently produce a naive-γ₅ (NDR) "
        "result stamped as a different scheme. Refusing rather than lying.",
        context={
            "requested": scheme,
            "implemented": sorted(GAMMA5_IMPLEMENTED),
        },
        user_instruction=(
            "FormCalc 9.10 computes with native anticommuting γ₅ (NDR). Use "
            "--gamma5 naive. HV/BMHV/Larin are not wired through CalcFeynAmp "
            "(see STEP3-DESIGN.md Decision 1); no complete implementation exists "
            "in this toolkit yet."
        ),
    )
    sys.exit(1)


# ── Argument parsing ───────────────────────────────────────────────────────────

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="run_formcalc.py",
        description="FormCalc amplitude reducer — /formcalc reduce",
    )
    sub = p.add_subparsers(dest="subcmd")
    reduce_p = sub.add_parser("reduce", help="Reduce a FeynAmpList.m with FormCalc")
    reduce_p.add_argument("--feynamp", required=True, help="Path to FeynAmpList.m")
    reduce_p.add_argument("--process", required=True, help="Path to ProcessSpec.json")
    reduce_p.add_argument("--output-dir", default="formcalc_output", help="Output directory")
    reduce_p.add_argument(
        "--reg",
        choices=list(REGULATORS),
        default="dimreg",
        help="Dimensional regulator",
    )
    reduce_p.add_argument(
        "--gamma5",
        choices=list(GAMMA5_SCHEMES),
        default=None,
        help="γ₅ renormalisation scheme (required if amplitude contains γ₅)",
    )
    reduce_p.add_argument(
        "--fermion-chains",
        choices=["weyl", "dirac"],
        default="weyl",
        dest="fermion_chains",
    )
    reduce_p.add_argument(
        "--dimension",
        choices=["4", "D"],
        default="D",
        dest="dimension",
    )
    reduce_p.add_argument(
        "--force",
        action="store_true",
        help="Ignore cache and rerun",
    )
    args = p.parse_args(argv)
    if args.subcmd is None:
        p.print_help()
        sys.exit(1)
    return args


# ── FeynArts version gate ──────────────────────────────────────────────────────

def check_feynarts_version(meta_path: Path):
    """Read FeynAmpList.meta.json and assert feynarts_version in supported set."""
    if not meta_path.exists():
        emit_blocker(
            "FORMCALC_FEYNARTS_VERSION_INCOMPATIBLE",
            "fatal",
            f"FeynAmpList.meta.json not found: {meta_path}",
            user_instruction="Run /feynarts generate to produce FeynAmpList.m + sidecar.",
        )
        sys.exit(1)
    with open(meta_path) as f:
        meta = json.load(f)
    version = meta.get("feynarts_version", "")
    if version not in SUPPORTED_FEYNARTS_VERSIONS:
        emit_blocker(
            "FORMCALC_FEYNARTS_VERSION_INCOMPATIBLE",
            "fatal",
            f"FeynArts version '{version}' is not supported by this FormCalc skill.",
            context={
                "found": version,
                "supported": sorted(SUPPORTED_FEYNARTS_VERSIONS),
            },
            user_instruction=(
                f"Supported: {sorted(SUPPORTED_FEYNARTS_VERSIONS)}. "
                "Regenerate with a supported FeynArts version via _shared/installs/feynarts."
            ),
        )
        sys.exit(1)
    return version


# ── γ₅ static check ───────────────────────────────────────────────────────────

def run_gamma5_check(feynamp_path: Path, wolfram_bin: str, gamma5_scheme: Optional[str]) -> bool:
    """
    Run gamma5_static_check.wls.  Returns True if chirality/γ₅ found.
    If found and no scheme given → emit fatal blocker + exit.
    """
    check_script = SCRIPT_DIR / "gamma5_static_check.wls"
    if not check_script.exists():
        # Skip if script not yet present (defensive)
        return False

    try:
        result = subprocess.run(
            [wolfram_bin, "-script", str(check_script), str(feynamp_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        print("[formcalc] WARN: γ₅ check timed out; proceeding without check.", file=sys.stderr)
        return False

    has_chiral = result.returncode == 1  # exit 1 = chiral found
    if has_chiral and gamma5_scheme is None:
        emit_blocker(
            "FORMCALC_G5_SCHEME_REQUIRED",
            "fatal",
            "Amplitude contains γ₅ / chirality projectors; --gamma5 <scheme> is required.",
            hint=f"Add --gamma5 {{{'|'.join(sorted(GAMMA5_SCHEMES))}}} to your command.",
        )
        sys.exit(1)
    return has_chiral


# ── Cache key ─────────────────────────────────────────────────────────────────

def compute_cache_key(
    feynamp_path: Path,
    processspec_path: Path,
    reg: str,
    gamma5: Optional[str],
    fc_version: str,
    form_version: str,
    lt_version: str,
) -> str:
    """Compute SHA256 cache key per plan §5."""
    from cache_key import compute as _compute_cache_key_impl
    return _compute_cache_key_impl(
        feynamp_path=feynamp_path,
        processspec_path=processspec_path,
        reg=reg,
        gamma5=gamma5 or "none",
        formcalc_version=fc_version,
        form_version=form_version,
        looptools_version=lt_version,
    )


def _read_build_key(output_dir: Path) -> str:
    bk = output_dir / ".build_key"
    if bk.exists():
        return bk.read_text().strip()
    return ""


def _cache_hit(output_dir: Path, cache_key: str) -> bool:
    """Cache hit requires amp_reduced.m + sidecar + .build_key all present and matching."""
    required = [
        output_dir / "amp_reduced.m",
        output_dir / "amp_reduced.meta.json",
        output_dir / ".build_key",
    ]
    for f in required:
        if not f.exists():
            return False
    return _read_build_key(output_dir) == cache_key


# ── Symlink helpers ────────────────────────────────────────────────────────────

def _make_input_symlinks(output_dir: Path, feynamp_path: Path, processspec_path: Path):
    """Create output_dir/input/{FeynAmpList.m,FeynAmpList.meta.json,ProcessSpec.json}."""
    input_dir = output_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    feynamp_path = feynamp_path.resolve()
    processspec_path = processspec_path.resolve()
    meta_path = feynamp_path.parent / (feynamp_path.stem + ".meta.json")

    for src, name in [
        (feynamp_path, "FeynAmpList.m"),
        (meta_path, "FeynAmpList.meta.json"),
        (processspec_path, "ProcessSpec.json"),
    ]:
        dest = input_dir / name
        if dest.exists() or dest.is_symlink():
            dest.unlink()
        if src.exists():
            dest.symlink_to(src)
        else:
            # Create placeholder for missing optional files
            if name != "FeynAmpList.meta.json":
                raise FileNotFoundError(f"Required input not found: {src}")
    return input_dir


# ── Main ───────────────────────────────────────────────────────────────────────

def main(argv=None):
    args = parse_args(argv)

    # Refuse-to-lie (R1): reject any γ₅ scheme not wired to CalcFeynAmp before
    # doing any work, so an unimplemented scheme can never reach the sidecar.
    check_gamma5_implemented(args.gamma5)

    config = read_config()

    feynamp_path = Path(args.feynamp).resolve()
    processspec_path = Path(args.process).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate inputs exist.
    if not feynamp_path.exists():
        emit_blocker("FORMCALC_PATH_INVALID", "fatal", f"FeynAmpList.m not found: {feynamp_path}")
        sys.exit(1)
    if not processspec_path.exists():
        emit_blocker("FORMCALC_PATH_INVALID", "fatal", f"ProcessSpec.json not found: {processspec_path}")
        sys.exit(1)

    # Config checks.
    wolfram_bin = config.get("wolfram_engine_path", "") or ""
    if not wolfram_bin or not Path(wolfram_bin).exists():
        wolfram_bin = subprocess.run(
            ["which", "wolframscript"], capture_output=True, text=True
        ).stdout.strip()
    if not wolfram_bin or not Path(wolfram_bin).exists():
        emit_blocker("WOLFRAM_KERNEL_ABSENT", "fatal", "wolframscript not found.")
        sys.exit(1)

    fc_path = config.get("formcalc_path", "") or ""
    if not fc_path or not Path(fc_path, "FormCalc.m").exists():
        emit_blocker(
            "FORMCALC_PATH_INVALID",
            "fatal",
            "formcalc_path not set or FormCalc.m missing.",
            user_instruction="Run _shared/installs/formcalc first.",
        )
        sys.exit(1)

    form_binary = config.get("form_binary", "") or ""
    if form_binary and not Path(form_binary).exists():
        emit_blocker(
            "FORMCALC_SMOKE_TEST_FAILED",
            "fatal",
            f"form_binary not found: {form_binary}",
        )
        sys.exit(1)

    fc_version = config.get("formcalc_version", "9.10")
    form_version = config.get("form_version", "4.3.1")
    lt_version = config.get("looptools_version", "9.10")

    # Create input symlinks.
    _make_input_symlinks(output_dir, feynamp_path, processspec_path)
    meta_path = feynamp_path.parent / (feynamp_path.stem + ".meta.json")

    # FeynArts version gate.
    fa_version = check_feynarts_version(meta_path)

    # γ₅ static check.
    run_gamma5_check(feynamp_path, wolfram_bin, args.gamma5)

    # Cache key.
    from cache_key import compute as _ck_compute
    cache_key = _ck_compute(
        feynamp_path=feynamp_path,
        processspec_path=processspec_path,
        reg=args.reg,
        gamma5=args.gamma5 or "none",
        formcalc_version=fc_version,
        form_version=form_version,
        looptools_version=lt_version,
    )

    if not args.force and _cache_hit(output_dir, cache_key):
        print(f"[formcalc] Cache hit: {output_dir}", file=sys.stderr)
        # Still emit summary.
        print(json.dumps({"status": "ok", "cached": True, "output_dir": str(output_dir)}))
        return 0

    # Prepare kinematics.m
    from prepare_kinematics import generate_kinematics_m
    kinematics_content = generate_kinematics_m(processspec_path)
    kinematics_path = output_dir / "kinematics.m"
    kinematics_path.write_text(kinematics_content, encoding="utf-8")

    # Run driver.
    ts = time.strftime("%Y%m%dT%H%M%S")
    run_dir = output_dir / "run" / ts
    run_dir.mkdir(parents=True, exist_ok=True)

    driver_script = SCRIPT_DIR / "run_calcfeynamp.wls"
    driver_args = [
        wolfram_bin,
        "-script",
        str(driver_script),
        str(feynamp_path),
        str(kinematics_path),
        str(output_dir),
        fc_path,
        form_binary or "",
        args.fermion_chains,
        args.dimension,
        str(run_dir),
    ]
    try:
        t0 = time.time()
        result = subprocess.run(
            driver_args,
            capture_output=True,
            text=True,
            timeout=3600,
        )
        wall_clock = time.time() - t0
    except subprocess.TimeoutExpired:
        emit_blocker("FORMCALC_DRIVER_FAILED", "fatal", "run_calcfeynamp.wls timed out")
        sys.exit(1)

    if result.returncode != 0:
        emit_blocker(
            "FORMCALC_DRIVER_FAILED",
            "fatal",
            f"run_calcfeynamp.wls exited {result.returncode}",
            context={"exit_code": result.returncode, "stderr": result.stderr[-2000:]},
        )
        sys.exit(1)

    # ── Require the expected artifact ─────────────────────────────────────────
    # The Wolfram driver can exit 0 without producing amp_reduced.m: FormCalc.m
    # calls Abort[] (not Exit[1]) when ReadForm cannot Install, and an Abort at
    # top level of a -script Module ends the run with exit status 0. Trusting
    # the exit code alone therefore reports a green sidecar for a reduction that
    # never happened (the "silent success" defect). Make a missing/empty
    # amp_reduced.m a loud, fatal, recoverable blocker instead, and scan the
    # driver log to name the underlying cause (ReadForm / MathLink failure).
    amp_reduced_path = output_dir / "amp_reduced.m"
    if not amp_reduced_path.exists() or amp_reduced_path.stat().st_size == 0:
        driver_log = "\n".join(
            part for part in (result.stdout or "", result.stderr or "") if part
        )
        cause = _diagnose_missing_amp_reduced(driver_log)
        emit_blocker(
            "FORMCALC_REDUCE_NO_OUTPUT",
            "recoverable",
            "FormCalc driver exited 0 but produced no amp_reduced.m "
            f"({'missing' if not amp_reduced_path.exists() else 'empty'}); "
            "the reduction did not run.",
            context={
                "output_dir": str(output_dir),
                "cause": cause,
                "log_tail": driver_log[-2000:],
                "run_dir": str(run_dir),
            },
            user_instruction=(
                "ReadForm / FORM failed to start, so CalcFeynAmp aborted. "
                "Verify <formcalc_path>/$SystemID/ReadForm resolves to the "
                "compiled MathLink executable (FormCalc.m loads it from "
                "$FormCalcDir/$SystemID, not $FormCalcDir/bin/$SystemID); "
                "reinstall via _shared/installs/formcalc if it is missing."
                if cause == "readform_notcompiled"
                else "Inspect the driver log tail and run/<ts>/ for the failure."
            ),
        )
        sys.exit(1)

    # Parse summary + PV heads.
    from parse_summary import parse_summary
    summary = parse_summary(amp_reduced_path)

    # Write sidecar.
    from write_sidecar import write_sidecar
    feynamp_hash = hashlib.sha256(feynamp_path.read_bytes()).hexdigest()
    processspec_hash = hashlib.sha256(
        json.dumps(json.loads(processspec_path.read_text()), sort_keys=True).encode()
    ).hexdigest()

    # Determine Wolfram version.
    wolfram_ver = ""
    try:
        wv = subprocess.run(
            [wolfram_bin, "-code", 'Print[$VersionNumber]'],
            capture_output=True, text=True, timeout=30
        )
        wolfram_ver = wv.stdout.strip().split("\n")[0].strip()
        # Normalise to major.minor
        if wolfram_ver and wolfram_ver.replace(".", "").isdigit() is False:
            wolfram_ver = ""
    except Exception:
        wolfram_ver = ""

    import datetime
    sidecar_data = {
        "schema_version": "amp_reduced.meta/v1",
        "formcalc_version": fc_version,
        "form_version": form_version,
        "looptools_version": lt_version,
        # Honest by construction: check_gamma5_implemented() has already rejected
        # anything but naive/None, and CalcFeynAmp was invoked with FormCalc's NDR
        # default. So the effective scheme is always naive; the caveat below records
        # the naive == FormCalc-9.10-NDR-default equivalence (STEP3-DESIGN.md Dec. 1).
        "gamma5_scheme": args.gamma5 or "naive",
        "pv_heads": "formcalc-native",
        "abbreviations_manifest": "",
        "input_hashes": {
            "feynamplist_m": feynamp_hash,
            "processspec_json": processspec_hash,
        },
        "kinematic_limit": json.loads(processspec_path.read_text()).get("kinematic_limit", "general"),
        "ir_flags": {
            "ir_divergent": summary.get("ir_divergent", False),
            "uv_regularized": summary.get("uv_regularized", False),
        },
        "caveats": _build_caveats(args.reg, args.gamma5 or "naive"),
        "produced_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "wolfram_version_major_minor": wolfram_ver or "0.0",
    }

    write_sidecar(output_dir / "amp_reduced.meta.json", sidecar_data)

    # Write .build_key last (atomic).
    _write_build_key_atomic(output_dir, cache_key)

    print(json.dumps({
        "status": "ok",
        "cached": False,
        "output_dir": str(output_dir),
        "wall_clock_s": round(wall_clock, 2),
    }))
    return 0


def _atomic_write_via_shell(dest: Path, content: str) -> None:
    """Write content to dest via the Phase-0 atomic_write.sh helper (atomic_write_stdin).

    Sources _common.sh then atomic_write.sh, then pipes content on stdin to
    atomic_write_stdin <dest>.  All atomicity discipline (tmp + fsync + rename +
    dir-fsync) is centralised in plugins/shared/install-helpers/atomic_write.sh.
    """
    import tempfile
    atomic_write_sh = SHARED_HELPERS / "atomic_write.sh"
    common_sh = SHARED_HELPERS / "_common.sh"
    if not atomic_write_sh.exists():
        raise FileNotFoundError(f"atomic_write.sh not found: {atomic_write_sh}")
    if not common_sh.exists():
        raise FileNotFoundError(f"_common.sh not found: {common_sh}")
    # Write a tiny wrapper script that sources the helpers and calls atomic_write_stdin.
    # Using a temp file for the script keeps stdin free for the content pipe.
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
            ["bash", sf_path],
            input=content,
            text=True,
            capture_output=True,
        )
    finally:
        os.unlink(sf_path)
    if result.returncode != 0:
        raise RuntimeError(
            f"atomic_write_via_shell failed for {dest}: {result.stderr.strip()}"
        )



def _diagnose_missing_amp_reduced(driver_log: str) -> str:
    """Classify why amp_reduced.m is absent by scanning the Wolfram driver log.

    Returns a short cause tag used in the FORMCALC_REDUCE_NO_OUTPUT blocker
    context. The dominant real-world cause is a broken ReadForm MathLink
    executable (install-layout regression): FormCalc.m emits
    ReadForm::notcompiled / LinkOpen::linke and Abort[]s, so no reduction runs.
    """
    log = driver_log or ""
    readform_markers = (
        "ReadForm::notcompiled",
        "could not be installed",
        "LinkOpen::linke",
        "Could not find MathLink executable",
        "Could not find installable MathLink",
    )
    if any(marker in log for marker in readform_markers):
        return "readform_notcompiled"
    if "CalcFeynAmp" in log and "failed" in log.lower():
        return "calcfeynamp_failed"
    if "Needs[FormCalc] failed" in log:
        return "formcalc_load_failed"
    return "unknown"


def _build_caveats(reg: str, gamma5: str = "naive") -> list:
    caveats = []
    if reg in ("cdr", "thv"):
        caveats.append("FORMCALC_REG_UNVALIDATED")
    # Record what the γ₅ stamp actually means (STEP3-DESIGN.md Decision 1): naive
    # is not a scheme option forwarded to CalcFeynAmp — it names FormCalc 9.10's
    # native anticommuting-γ₅ (NDR) default, which is the only reduction ever run.
    # Making the equivalence explicit keeps the sidecar honest rather than implying
    # a scheme choice was made and applied.
    if gamma5 == "naive":
        caveats.append(
            "GAMMA5_NDR_FORMCALC_DEFAULT: gamma5_scheme=naive denotes FormCalc "
            "9.10 native anticommuting-gamma5 (NDR); CalcFeynAmp is invoked with "
            "no gamma5 scheme option, so this stamp reflects the actual reduction. "
            "hv/bmhv/larin are not implemented (see STEP3-DESIGN.md Decision 1)."
        )
    return caveats


def _write_build_key_atomic(output_dir: Path, cache_key: str):
    """Write .build_key atomically via the Phase-0 atomic_write.sh helper.

    Shells out to atomic_write_stdin so all atomicity discipline (tmp + fsync +
    rename + dir-fsync) is centralised in plugins/shared/install-helpers/atomic_write.sh.
    """
    dest = output_dir / ".build_key"
    _atomic_write_via_shell(dest, cache_key + "\n")


if __name__ == "__main__":
    sys.exit(main())
