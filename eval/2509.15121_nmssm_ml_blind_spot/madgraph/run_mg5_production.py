"""
OFFLINE script to run MadGraph5 and cache production cross sections.
arXiv:2509.15121, pp > chi1+ chi20 j at BP1-3.

USAGE (offline only, never invoked by harness):
    python madgraph/run_mg5_production.py [--mg5 MG5_PATH] [--output cached_sigma_prod.json]

OUTPUT:
    madgraph/cached_sigma_prod.json — committed only if sigma_fb within 5% of 105.1 fb.

HARNESS INTEGRATION:
    The harness NEVER imports this script. The cached JSON is the only runtime artifact.
    Per plan §18 (S18): the t2_nmssm_sigma_prod_bp1_3 YAML row is authored only when
    the cache exists and sigma_fb is within 5% of 105.1 fb.

VALIDATION CHECK (must pass before committing):
    python -c "
    import json, pathlib, sys
    p = pathlib.Path('eval/2509.15121_nmssm_ml_blind_spot/madgraph/cached_sigma_prod.json')
    if not p.exists():
        print('cache absent → row NOT authored'); sys.exit(0)
    d = json.loads(p.read_text())
    assert 'BP1_3' in d, 'BP1_3 missing'
    s = d['BP1_3']['sigma_fb']
    assert abs(s - 105.1) / 105.1 < 0.05, f'σ_cached={s} disagrees with paper 105.1 by >5%'
    print('row AUTHORIZED')
    "
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def run_mg5(mg5_executable: str, proc_card: Path, param_card: Path,
            run_card: Path, output_dir: Path) -> dict:
    """
    Run MadGraph5 on the provided cards and return the parsed cross section.

    Parameters
    ----------
    mg5_executable : str — path to mg5_aMC
    proc_card : Path — process card
    param_card : Path — SLHA-1 parameter card
    run_card : Path — run configuration card
    output_dir : Path — temporary output directory for MG5

    Returns
    -------
    dict with keys 'sigma_fb', 'mc_stat_err_fb'
    """
    # Create MG5 input script
    mg5_input = f"""
import model nmssm
generate p p > x1+ n2 j
output {output_dir}
launch {output_dir}
   {param_card}
   {run_card}
0
"""
    input_script = Path("/tmp/nmssm_mg5_run.dat")
    input_script.write_text(mg5_input)

    result = subprocess.run(
        [mg5_executable, str(input_script)],
        capture_output=True, text=True, timeout=3600
    )

    if result.returncode != 0:
        print(f"MG5 FAILED (returncode={result.returncode})")
        print(result.stderr[-2000:])
        sys.exit(1)

    # Parse cross section from MG5 output
    sigma_fb = None
    mc_err_fb = None
    for line in result.stdout.split("\n"):
        # Pattern: "  Cross-section :   1.051e+02 +- 5.25e-01 pb"
        m = re.search(r"Cross-section\s*:\s*([\d.e+\-]+)\s*\+-\s*([\d.e+\-]+)\s*(pb|fb)", line)
        if m:
            val = float(m.group(1))
            err = float(m.group(2))
            unit = m.group(3)
            if unit == "pb":
                val *= 1000.0
                err *= 1000.0
            sigma_fb = val
            mc_err_fb = err
            break

    if sigma_fb is None:
        print("ERROR: Could not parse cross section from MG5 output")
        print("Last 50 lines of output:")
        for line in result.stdout.split("\n")[-50:]:
            print(f"  {line}")
        sys.exit(1)

    return {"sigma_fb": sigma_fb, "mc_stat_err_fb": mc_err_fb}


def main():
    parser = argparse.ArgumentParser(description="Run MG5 for NMSSM production cross section")
    parser.add_argument("--mg5", default="mg5_aMC", help="MadGraph5 executable")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent / "cached_sigma_prod.json"),
        help="Output JSON file path"
    )
    args = parser.parse_args()

    here = Path(__file__).parent
    proc_card = here / "proc_card.dat"
    param_card = here / "param_card_BP1_3.dat"
    run_card = here / "run_card.dat"
    output_dir = Path("/tmp/nmssm_mg5_output")

    print(f"Running MadGraph5: {args.mg5}")
    print(f"Process: pp > chi1+ chi20 j (nmssm model)")
    print(f"Benchmark: BP1-3 (mu_eff=161.8, kappa=0.01243, M1=500)")

    xsec = run_mg5(args.mg5, proc_card, param_card, run_card, output_dir)

    cache = {
        "BP1_3": {
            "process": "pp>chi1+chi20j",
            "sqrt_s": 14000,
            "pdf": "NNPDF30_lo_as_0130",
            "scale": "HT/2",
            "order": "LO",
            "events": 50000,
            "sigma_fb": xsec["sigma_fb"],
            "mc_stat_err_fb": xsec["mc_stat_err_fb"],
        }
    }

    # Validate against paper value before writing
    sigma = cache["BP1_3"]["sigma_fb"]
    paper_sigma = 105.1
    rel_diff = abs(sigma - paper_sigma) / paper_sigma
    print(f"\nComputed sigma = {sigma:.3f} fb")
    print(f"Paper sigma    = {paper_sigma:.3f} fb")
    print(f"Relative diff  = {rel_diff:.3f}")

    if rel_diff > 0.05:
        print(f"\nERROR: sigma_cached={sigma:.2f} disagrees with paper 105.1 by >5%!")
        print("Per plan §6.2: do NOT commit cached_sigma_prod.json. Escalate to Yianni.")
        sys.exit(2)

    with open(args.output, "w") as f:
        json.dump(cache, f, indent=2)
    print(f"\nCache written to {args.output}")
    print("AUTHORIZED: Within 5% of paper value. Commit cache and add YAML row.")


if __name__ == "__main__":
    main()
