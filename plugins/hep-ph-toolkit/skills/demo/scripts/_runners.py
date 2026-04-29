"""Thin wrappers around external MC tools.

Every physics number in the demo comes from one of these calls. The wrappers
deliberately do nothing beyond:
  - building the tool's session script,
  - launching the tool's binary,
  - parsing the tool's stdout for the observable(s).

No matrix elements or Boltzmann evolutions are reimplemented here — that's
the "augment not replace" rule the project was built around.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from _cache import ensure_spheno, load_config, run_dir


# ---------------------------------------------------------------------------
# SPheno
# ---------------------------------------------------------------------------

def run_spheno(model_hash: str, param_hash: str, slha_in: str) -> Path:
    """Run the SARAH-produced SPheno binary on an SLHA input card.

    Returns the path to the spectrum.slha file. Cached: if spectrum.slha
    already exists in the run dir, we skip the launch.
    """
    spheno = ensure_spheno(model_hash)
    rd = run_dir(model_hash, param_hash)
    rd.mkdir(parents=True, exist_ok=True)
    spectrum = rd / "spectrum.slha"
    if spectrum.exists():
        return spectrum

    in_card = rd / "LesHouches.in"
    in_card.write_text(slha_in)

    # SPheno convention: `SPheno <input_card> <output_card>`
    result = subprocess.run(
        [str(spheno), str(in_card), str(spectrum)],
        capture_output=True, text=True, timeout=120,
        cwd=str(rd),
    )
    if result.returncode != 0 or not spectrum.exists():
        sys.stderr.write(result.stdout[-2000:])
        sys.stderr.write(result.stderr[-2000:])
        raise SystemExit(
            f"SPheno failed for model-hash={model_hash} param-hash={param_hash}. "
            "See stderr above. Do not fall back to analytic spectrum."
        )
    return spectrum


# ---------------------------------------------------------------------------
# MadGraph5_aMC@NLO via /madgraph
# ---------------------------------------------------------------------------

def run_mg5(session_script: str, workdir: Path, timeout: int = 300) -> str:
    """Invoke mg5_aMC with a session script. Returns stdout for parsing."""
    cfg = load_config()
    mg5_bin = Path(cfg["madgraph_path"]).expanduser()
    if not mg5_bin.exists():
        raise SystemExit(
            f"MadGraph binary not found at {mg5_bin}. Re-run /install."
        )

    workdir.mkdir(parents=True, exist_ok=True)
    cmd_file = workdir / "mg5_cmd.txt"
    cmd_file.write_text(session_script)

    result = subprocess.run(
        [str(mg5_bin), str(cmd_file)],
        capture_output=True, text=True, timeout=timeout,
        cwd=str(workdir),
    )
    (workdir / "mg5_stdout.log").write_text(result.stdout)
    if result.returncode != 0:
        sys.stderr.write(result.stdout[-2000:])
        sys.stderr.write(result.stderr[-2000:])
        raise SystemExit(
            "MadGraph failed. Per augment-don't-replace, the demo does not "
            "fall back to analytic cross-sections. Inspect the log above."
        )
    return result.stdout


CROSS_SECTION_RE = re.compile(
    r"Cross-section\s*:\s*([\deE.+-]+)\s*\+-\s*([\deE.+-]+)\s*pb"
)


def parse_xsec_pb(stdout: str) -> float:
    """Extract the last reported cross-section (pb) from an MG5 run."""
    matches = CROSS_SECTION_RE.findall(stdout)
    if not matches:
        raise SystemExit(
            "Could not parse cross-section from MG5 stdout. MG5 output "
            "format may have changed; update CROSS_SECTION_RE in _runners.py."
        )
    return float(matches[-1][0])


# ---------------------------------------------------------------------------
# MadDM
# ---------------------------------------------------------------------------

def run_maddm(
    ufo_path: Path,
    param_card: Path,
    observables: list[str],
    workdir: Path,
    dm_pdg: int | None = None,
    timeout: int = 600,
) -> dict:
    """Launch a MadDM session and parse maddm_results.txt.

    observables: subset of {"relic", "direct_detection", "indirect_detection"}.
    Returns dict with keys like omega_h2, sigma_si_proton, sigmav_total.
    """
    cfg = load_config()
    mg5_bin = Path(cfg["madgraph_path"]).expanduser()
    if not mg5_bin.exists():
        raise SystemExit(
            f"MG5 binary not found at {mg5_bin}. MadDM runs inside MG5 — "
            "re-run /install."
        )

    workdir.mkdir(parents=True, exist_ok=True)
    proc_dir = workdir / "maddm_proc"

    lines = [
        "install maddm",
        f"import model {ufo_path}",
    ]
    if dm_pdg is not None:
        lines.append(f"define darkmatter {dm_pdg}")
    lines += [
        "generate_maddm",
        f"output {proc_dir}",
        f"launch {proc_dir}",
    ]
    flags = {
        "relic": "relic_density",
        "direct_detection": "direct_detection",
        "indirect_detection": "indirect_detection",
    }
    for key, flag in flags.items():
        lines.append(f"  set {flag} {'ON' if key in observables else 'OFF'}")
    lines.append(f"  {param_card}")
    lines.append("  done")

    session = "\n".join(lines) + "\n"
    cmd_file = workdir / "maddm_cmd.txt"
    cmd_file.write_text(session)

    # --mode=maddm loads the MadDM plugin into the MG5 interpreter. Bare
    # mg5_aMC <script> runs the base interpreter and `generate
    # relic_density` raises InvalidCmd. See
    # plugins/hep-ph-toolkit/skills_shared/installs/maddm/references/maddm-workarounds.md §8.
    result = subprocess.run(
        [str(mg5_bin), "--mode=maddm", str(cmd_file)],
        capture_output=True, text=True, timeout=timeout,
        cwd=str(workdir),
    )
    (workdir / "maddm_stdout.log").write_text(result.stdout)
    if result.returncode != 0:
        sys.stderr.write(result.stdout[-2000:])
        sys.stderr.write(result.stderr[-2000:])
        raise SystemExit("MadDM session failed. See log above.")

    results_file = next(proc_dir.rglob("maddm_results.txt"), None)
    if results_file is None:
        raise SystemExit(
            f"MadDM ran but maddm_results.txt not found under {proc_dir}."
        )

    # Delegate parsing to the existing maddm skill helper to keep output-
    # format knowledge in one place.
    from_maddm = _parse_maddm_results(results_file)
    return from_maddm


def _parse_maddm_results(path: Path) -> dict:
    text = path.read_text()
    out: dict = {}
    m = re.search(r"Omega\s*h\^?2\s*[=:]\s*([\deE.+-]+)", text)
    if m:
        out["omega_h2"] = float(m.group(1))
    # MadDM 3.2 emits per-nucleon σ as `SigmaN_SI_p = [σ, exp_limit]` etc.
    # Capture only the first bracket element (the predicted σ at this mass).
    for maddm_key, out_key in (
        ("SigmaN_SI_p", "sigma_si_proton"),
        ("SigmaN_SI_n", "sigma_si_neutron"),
        ("SigmaN_SD_p", "sigma_sd_proton"),
        ("SigmaN_SD_n", "sigma_sd_neutron"),
    ):
        mm = re.search(
            rf"^{maddm_key}\s*=\s*\[\s*([\deE.+-]+)",
            text, re.MULTILINE,
        )
        if mm:
            out[out_key] = float(mm.group(1))
    sv = re.search(r"<sigma\s*v>\s*(?:total)?\s*[=:]\s*([\deE.+-]+)", text)
    if sv:
        out["sigmav_total"] = float(sv.group(1))
    return out
