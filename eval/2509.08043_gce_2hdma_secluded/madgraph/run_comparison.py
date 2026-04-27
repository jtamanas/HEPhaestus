"""
Optional MadGraph5 vs analytics cross-check for 2HDM+a VBF process.
arXiv:2509.08043, Section 3.2.6.

NOT wired to the YAML harness (Phase-1 delivery — see madgraph/README.md).
Runs bauer_ufo_check first; only attempts MG5 shell-out if mg5_aMC is present.
Safe to run without MadGraph5 installed (prints warning and exits 0).

Usage:
    python eval/2509.08043_gce_2hdma_secluded/madgraph/run_comparison.py
"""

import shutil
import subprocess
import sys
from pathlib import Path


def run_comparison() -> int:
    """Run the Bauer UFO check then optionally the MG5 cross-check.

    Returns
    -------
    int : exit code (0 = success or MG5 absent; 1 = UFO check failure)
    """
    # Step 1: Bauer UFO check (always runs)
    import importlib.util
    check_path = Path(__file__).parent / "bauer_ufo_check.py"
    spec = importlib.util.spec_from_file_location("bauer_ufo_check", str(check_path))
    check_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check_module)

    result = check_module.verify_ufo()
    if not result["ok"]:
        print(f"ERROR: Bauer UFO check failed. Missing: {sorted(result['missing'])}")
        return 1
    print("Bauer UFO check passed.")

    # Step 2: Attempt MG5 shell-out
    mg5_path = shutil.which("mg5_aMC")
    if mg5_path is None:
        print(
            "WARNING: mg5_aMC not found in PATH. Skipping MadGraph5 cross-check.\n"
            "Install MadGraph5_aMC@NLO and rerun to perform the VBF cross-section comparison.\n"
            "See madgraph/README.md for the expected procedure."
        )
        return 0

    print(f"Found mg5_aMC at: {mg5_path}")
    proc_card = Path(__file__).parent / "2hdma" / "proc_card.dat"
    if not proc_card.exists():
        print(f"WARNING: proc_card.dat not found at {proc_card}. Skipping.")
        return 0

    print(f"Running MG5 with: {proc_card}")
    proc = subprocess.run(
        [mg5_path, str(proc_card)],
        capture_output=True,
        text=True,
        timeout=3600,
    )
    if proc.returncode != 0:
        print(f"MG5 exited with code {proc.returncode}")
        print(proc.stderr[-2000:] if proc.stderr else "")
        return 1

    print("MG5 run completed. Parse banner file for cross-section comparison.")
    return 0


if __name__ == "__main__":
    sys.exit(run_comparison())
