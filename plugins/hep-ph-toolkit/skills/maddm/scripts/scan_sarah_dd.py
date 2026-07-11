#!/usr/bin/env python3
"""scan_sarah_dd.py — 1-D parameter scan of a SARAH model's direct-detection σ.

The smallest composable driver that chains the pieces a SARAH-model DD scan
needs, so agents stop hand-rolling the loop (see maddm/references/scanning.md,
"SARAH-model DD scans"). Each scan point is:

    spectrum  (spheno-build, analytic backend, --no-register)   [~0.3 s]
        │  per-point SPheno.spc under $STATE_ROOT
        ▼
    MadDM DD  (two-phase SLHA overlay + complete_sarah_param_card              )
              (+ Block BSMPARAMS gate; fresh output dir per point at RUN time  )   [~10 s]
        │  MadDM_results.txt
        ▼
    parse     (gamlike parse_maddm_results.py)  →  σ_SI(p/n), σ_SD(p/n)
        │
        ▼
    collect   →  scan_results.json  +  scan_results.csv

Design notes (why this and not maddm's simplified-model scan_grid.py):
  * A SARAH model's documented DD path is the two-phase overlay +
    `complete_sarah_param_card` + BSMPARAMS gate. `scan_grid.py`/`generate_batch`
    patch `set BLOCK PID` lines into a single-phase template that
    `generate_maddm_script` never emits — it does not fit this model class.
  * The scan variable can drive DERIVED spectrum params via `--param NAME=EXPR`
    (EXPR is a math expression in the scan variable). The θ scan needs exactly
    this: yh1 = cos(θ), yh2 = sin(θ). A "scan one BLOCK:PID linearly" API cannot
    express it.
  * `--no-register` on every spectrum run keeps the scan from poisoning the
    global `latest_slha` pointer; each point's SLHA is fed to its own DD run by
    path, never via the convenience cache.
  * Fresh output dir per point (generate_maddm_script fresh=True → `!rm -rf`
    at RUN time) is the frozen-SI-staleness discipline; nothing is deleted at
    script-generation time.

Worked example (the blind-spot θ scan shape, MS=150, MPsi=500, y=1):

    python3 scan_sarah_dd.py singlet_doublet \\
        --scan theta=-0.17:-0.135:8 \\
        --param MS=150 --param MPsi=500 \\
        --param 'yh1=cos(theta)' --param 'yh2=sin(theta)' \\
        --dm-candidate chi1 --dm-name Chi1 \\
        --out-dir /tmp/theta_scan

Usage:
    python3 scan_sarah_dd.py <model> --scan VAR=start:stop:N \\
        --param NAME=EXPR [--param ...] --out-dir DIR [options]
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent          # .../maddm/scripts
_SKILLS_DIR = _SCRIPT_DIR.parent.parent                # .../skills
_SHARED_CONFIG = (
    _SKILLS_DIR.parent.parent / "shared" / "install-helpers" / "config_helpers.py"
)

# math namespace for --param expressions (no builtins → safe-ish local eval).
# Deliberately EXCLUDED: `nan`/`inf` (a --param landing on a non-finite value is
# an error, not an input — see the isfinite guard in eval_params) and the
# collision-prone short names `e`, `gamma`, `tau` — a typo'd or colliding bare
# name should raise NameError loudly, not silently resolve to Euler's number /
# the gamma function and compute garbage. `pi` is kept. Available names:
# everything else in the `math` module (cos, sin, sqrt, exp, log, pi, ...)
# plus the scan variable itself.
_EXCLUDED_EXPR_NAMES = {"nan", "inf", "e", "gamma", "tau"}
_MATH_NS = {
    k: getattr(math, k)
    for k in dir(math)
    if not k.startswith("_") and k not in _EXCLUDED_EXPR_NAMES
}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_scan_spec(spec: str) -> tuple[str, list[float]]:
    """`VAR=start:stop:N` → (VAR, [N linearly spaced values])."""
    if "=" not in spec:
        raise ValueError(f"--scan must be VAR=start:stop:N, got {spec!r}")
    var, rng = spec.split("=", 1)
    parts = rng.split(":")
    if len(parts) != 3:
        raise ValueError(f"--scan range must be start:stop:N, got {rng!r}")
    start, stop, n = float(parts[0]), float(parts[1]), int(parts[2])
    if n < 1:
        raise ValueError("N must be >= 1")
    if n == 1:
        return var.strip(), [start]
    return var.strip(), [start + i * (stop - start) / (n - 1) for i in range(n)]


def param_names(param_exprs: list[str]) -> list[str]:
    """The NAME parts of `NAME=EXPR` entries (no evaluation)."""
    names = []
    for pe in param_exprs:
        if "=" not in pe:
            raise ValueError(f"--param must be NAME=EXPR, got {pe!r}")
        names.append(pe.split("=", 1)[0].strip())
    return names


def eval_params(param_exprs: list[str], scan_var: str, value: float) -> dict[str, float]:
    """Evaluate each `NAME=EXPR` at scan_var=value into a spheno --params dict.

    Raises ValueError on a non-finite result (NaN/inf) — a spectrum input that
    is not a finite number is always a mistake, never physics.
    """
    out: dict[str, float] = {}
    ns = dict(_MATH_NS)
    ns[scan_var] = value
    for pe in param_exprs:
        if "=" not in pe:
            raise ValueError(f"--param must be NAME=EXPR, got {pe!r}")
        name, expr = pe.split("=", 1)
        val = float(eval(expr, {"__builtins__": {}}, ns))
        if not math.isfinite(val):
            raise ValueError(
                f"--param {name.strip()!r}={expr!r} evaluated to non-finite "
                f"{val!r} at {scan_var}={value!r}; spectrum inputs must be "
                "finite numbers."
            )
        out[name.strip()] = val
    return out


def dm_pdg_from_ufo(ufo_path: str | Path, name: str) -> int:
    text = (Path(ufo_path) / "particles.py").read_text()
    for m in re.finditer(
        r"pdg_code\s*=\s*(-?\d+)\s*,\s*\n\s*name\s*=\s*'([^']+)'", text
    ):
        if m.group(2) == name:
            return int(m.group(1))
    raise RuntimeError(f"particle {name!r} not found in {ufo_path}/particles.py")


def parse_mass_by_pdg(slha_path: str | Path, pdg: int) -> float:
    in_mass = False
    for line in Path(slha_path).read_text().splitlines():
        stripped = line.split("#")[0].strip()
        if line.strip().lower().startswith("block mass"):
            in_mass = True
            continue
        if in_mass and line.strip().lower().startswith("block "):
            break
        if in_mass and stripped:
            parts = stripped.split()
            if len(parts) >= 2 and int(parts[0]) == pdg:
                return float(parts[1])
    raise RuntimeError(f"pdg {pdg} not found in Block MASS of {slha_path}")


def run_point(args, maddm_run, slha_complete, mg5_bin, ufo_path, dm_pdg,
              scan_var, value, tag) -> dict:
    point_dir = Path(args.out_dir) / tag
    point_dir.mkdir(parents=True, exist_ok=True)
    # A per-value EXPR failure (bad name, domain error as the scan variable
    # crosses e.g. 0, non-finite result) marks THIS point failed and lets the
    # scan continue — same discipline as the downstream stage failures.
    try:
        params = eval_params(args.param, scan_var, value)
    except Exception as e:
        return {"scan_var": scan_var, "value": value, "tag": tag,
                "status": "failed", "stage": "param_eval",
                "stderr": f"{type(e).__name__}: {e}"}
    params_arg = ",".join(f"{k}={v!r}" for k, v in params.items())

    # ── Step 1: spectrum (analytic, --no-register so the scan never poisons
    #    the global latest_slha pointer) ────────────────────────────────────
    run_spheno = _SKILLS_DIR / "spheno-build" / "scripts" / "run_spheno.py"
    cmd = [sys.executable, str(run_spheno), args.model,
           "--skip-compile", "--no-register", "--params", params_arg]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    (point_dir / "spheno_stdout.json").write_text(proc.stdout)
    if proc.returncode != 0:
        return {"scan_var": scan_var, "value": value, "tag": tag,
                "status": "failed", "stage": "spheno", "stderr": proc.stderr}
    spheno = json.loads(proc.stdout.strip().splitlines()[-1])
    slha_path = spheno.get("slha_path")
    if not slha_path:
        return {"scan_var": scan_var, "value": value, "tag": tag,
                "status": "failed", "stage": "spheno_no_slha"}
    m_dm = parse_mass_by_pdg(slha_path, dm_pdg)

    # ── Step 2: MadDM DD, two-phase overlay (fresh dir per point at RUN time) ─
    dd_out = point_dir / "maddm_run_dd"
    setup_script, launch_script = maddm_run.generate_maddm_script(
        ufo_path=ufo_path, dm_candidate=args.dm_candidate, out_dir=str(dd_out),
        observables=["direct_detection"], split_for_param_overlay=True,
    )
    (point_dir / "setup.mg5").write_text(setup_script)
    (point_dir / "launch.mg5").write_text(launch_script)

    p1 = subprocess.run([mg5_bin, "--mode=maddm", str(point_dir / "setup.mg5")],
                        cwd=str(point_dir), capture_output=True, text=True)
    (point_dir / "mg5_setup.log").write_text(p1.stdout + "\n--STDERR--\n" + p1.stderr)
    if p1.returncode != 0:
        return {"scan_var": scan_var, "value": value, "tag": tag,
                "status": "failed", "stage": "mg5_setup"}

    card = dd_out / "Cards" / "param_card.dat"
    if not card.exists():
        return {"scan_var": scan_var, "value": value, "tag": tag,
                "status": "failed", "stage": "no_card"}
    shutil.copy(slha_path, card)
    completed = slha_complete.complete_sarah_param_card(card, ufo_path)
    if "block bsmparams" not in card.read_text().lower():
        return {"scan_var": scan_var, "value": value, "tag": tag,
                "status": "failed", "stage": "no_bsmparams"}

    p2 = subprocess.run([mg5_bin, "--mode=maddm", str(point_dir / "launch.mg5")],
                        cwd=str(point_dir), capture_output=True, text=True)
    (point_dir / "mg5_launch.log").write_text(p2.stdout + "\n--STDERR--\n" + p2.stderr)
    if p2.returncode != 0:
        return {"scan_var": scan_var, "value": value, "tag": tag,
                "status": "failed", "stage": "mg5_launch"}

    # ── Step 3: parse via gamlike ──────────────────────────────────────────
    results_txt = dd_out / "output" / "run_01" / "MadDM_results.txt"
    if not results_txt.exists():
        return {"scan_var": scan_var, "value": value, "tag": tag,
                "status": "failed", "stage": "no_results_txt"}
    gamlike_json = point_dir / "gamlike.json"
    parser = _SKILLS_DIR / "gamlike" / "scripts" / "parse_maddm_results.py"
    p3 = subprocess.run(
        [sys.executable, str(parser), str(results_txt), "--out", str(gamlike_json)],
        capture_output=True, text=True)
    if p3.returncode != 0:
        return {"scan_var": scan_var, "value": value, "tag": tag,
                "status": "failed", "stage": "gamlike", "stderr": p3.stderr}
    direct = json.loads(gamlike_json.read_text()).get("direct", {})
    si_p = direct.get("sigma_si_proton_cm2")
    si_n = direct.get("sigma_si_neutron_cm2")

    result = {
        "scan_var": scan_var, "value": value, "tag": tag, "status": "ok",
        **{k: params[k] for k in params},
        "m_dm_gev": m_dm,
        "sigma_si_proton_cm2": si_p,
        "sigma_si_neutron_cm2": si_n,
        "sigma_sd_proton_cm2": direct.get("sigma_sd_proton_cm2"),
        "sigma_sd_neutron_cm2": direct.get("sigma_sd_neutron_cm2"),
        "p_over_n": (si_p / si_n) if (si_p is not None and si_n) else None,
        "slha_path": slha_path,
        "maddm_results": str(results_txt),
        "completed_blocks": completed,
    }
    (point_dir / "result.json").write_text(json.dumps(result, indent=2))

    # ── Step 4: prune MG5 process bloat, keep result artifacts ─────────────
    if args.prune and dd_out.exists():
        for child in dd_out.iterdir():
            if child.name not in {"Cards", "output"}:
                shutil.rmtree(child, ignore_errors=True) if child.is_dir() else child.unlink(missing_ok=True)
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model", help="config slug, e.g. singlet_doublet")
    ap.add_argument("--scan", required=True, metavar="VAR=start:stop:N",
                    help="scan axis, e.g. theta=-0.17:-0.135:8")
    ap.add_argument("--param", action="append", default=[], metavar="NAME=EXPR",
                    help="spheno --params entry; EXPR is a math expression in the "
                         "scan var (repeatable). e.g. --param 'yh1=cos(theta)'")
    ap.add_argument("--out-dir", required=True, help="scratch dir for per-point artifacts")
    ap.add_argument("--dm-candidate", default="chi1",
                    help="MadDM DM candidate token (lowercased; default chi1)")
    ap.add_argument("--dm-name", default="Chi1",
                    help="UFO particle name for PDG lookup (default Chi1)")
    ap.add_argument("--ufo-path", default=None,
                    help="absolute UFO dir; default: $STATE_ROOT/models/<model>/<SarahName> "
                         "symlink, else config.models[model].ufo (validated)")
    ap.add_argument("--no-prune", dest="prune", action="store_false",
                    help="keep the full MG5 process dir per point (default: prune)")
    args = ap.parse_args()

    try:
        scan_var, values = parse_scan_spec(args.scan)
        names = param_names(args.param)
    except ValueError as e:
        ap.error(str(e))
    # A --param named like the scan variable would be silently shadowed in the
    # eval namespace (other EXPRs would still see the SCAN value, not the
    # override). Refuse up front rather than compute something ambiguous.
    if scan_var in names:
        ap.error(
            f"--param {scan_var!r} collides with the --scan variable; the scan "
            "drives that name. Rename the parameter or scan a different variable."
        )
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    config_helpers = _load(_SHARED_CONFIG, "config_helpers")
    config = config_helpers.load_config()
    state_root = config_helpers.STATE_ROOT
    mg5_bin = config.get("madgraph_path", "mg5_aMC")

    maddm_run = _load(_SCRIPT_DIR / "maddm_run.py", "maddm_run")
    slha_complete = _load(_SCRIPT_DIR / "slha_complete.py", "slha_complete")

    # Resolve UFO path: prefer explicit override, else config's ufo key run
    # through validate_ufo_path (warns on relative/hyphenated), else the
    # durable $STATE_ROOT symlink. dm-name is the SARAH particle name and the
    # symlink basename is the SARAH model name, which may differ — so if the
    # config path is clean we trust it; otherwise fall back to a scan of the
    # model dir for a hyphen-free symlink.
    if args.ufo_path:
        ufo_path = args.ufo_path
    else:
        cfg_ufo = (config.get("models", {}).get(args.model, {}) or {}).get("ufo")
        warnings = maddm_run.validate_ufo_path(cfg_ufo) if cfg_ufo else ["no config ufo"]
        if cfg_ufo and not warnings and Path(cfg_ufo).exists():
            ufo_path = cfg_ufo
        else:
            model_dir = state_root / "models" / args.model
            cand = sorted(
                p for p in model_dir.iterdir()
                if p.is_symlink() and "-" not in p.name
            ) if model_dir.exists() else []
            if not cand:
                print(f"ERROR: could not resolve a clean UFO path for {args.model!r}; "
                      f"pass --ufo-path explicitly.", file=sys.stderr)
                sys.exit(1)
            if len(cand) > 1:
                print(f"NOTE: {len(cand)} hyphen-free symlinks under {model_dir}: "
                      f"{[p.name for p in cand]}; choosing {cand[0].name!r} "
                      "(first in sorted order). Pass --ufo-path to override.",
                      file=sys.stderr)
            ufo_path = str(cand[0])
            print(f"resolved UFO from $STATE_ROOT symlink: {ufo_path}", file=sys.stderr)
    maddm_run.validate_ufo_path(ufo_path)  # final loud check
    dm_pdg = dm_pdg_from_ufo(ufo_path, args.dm_name)

    print(f"scan {scan_var} over {len(values)} points; ufo={ufo_path}; dm_pdg={dm_pdg}")
    results = []
    t0 = time.time()
    for i, value in enumerate(values):
        tag = f"pt_{i:03d}_{scan_var}_{value:+.6f}".replace(".", "p").replace("+", "p").replace("-", "m")
        rp = Path(args.out_dir) / tag / "result.json"
        if rp.exists():
            print(f"SKIP {tag} (has result.json)")
            results.append(json.loads(rp.read_text()))
            continue
        tp = time.time()
        r = run_point(args, maddm_run, slha_complete, mg5_bin, ufo_path, dm_pdg,
                      scan_var, value, tag)
        results.append(r)
        si = r.get("sigma_si_proton_cm2")
        si_s = f"{si:.3e}" if isinstance(si, (int, float)) else str(r.get("stage", "?"))
        print(f"[{i+1}/{len(values)}] {scan_var}={value:+.6f} status={r['status']} "
              f"sigma_SI(p)={si_s} ({time.time()-tp:.1f}s)")

    out_json = Path(args.out_dir) / "scan_results.json"
    out_json.write_text(json.dumps(results, indent=2))

    # CSV of the ok points
    ok = [r for r in results if r.get("status") == "ok"]
    if ok:
        cols = ["scan_var", "value", *sorted(names),
                "m_dm_gev", "sigma_si_proton_cm2", "sigma_si_neutron_cm2",
                "sigma_sd_proton_cm2", "sigma_sd_neutron_cm2", "p_over_n", "tag"]
        out_csv = Path(args.out_dir) / "scan_results.csv"
        with open(out_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(ok)
        print(f"wrote {out_csv}")
    print(f"wrote {out_json}  ({len(ok)}/{len(results)} ok, {time.time()-t0:.1f}s total)")


if __name__ == "__main__":
    main()
