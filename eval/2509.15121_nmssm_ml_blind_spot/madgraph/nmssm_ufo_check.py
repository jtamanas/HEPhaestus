"""
Offline sanity check for MadGraph5 nmssm UFO model availability.
arXiv:2509.15121 MadGraph5 benchmark.

USAGE (manual, offline only):
    python nmssm_ufo_check.py [MG5_PATH]

NOT imported by the harness. Run manually to verify MG5 setup before
running run_mg5_production.py.
"""

import subprocess
import sys
import os
from pathlib import Path


def check_mg5_nmssm(mg5_executable: str = "mg5_aMC") -> dict:
    """
    Check that MadGraph5 can find the built-in nmssm model.

    Parameters
    ----------
    mg5_executable : str — path to mg5_aMC binary

    Returns
    -------
    dict with keys: 'mg5_found', 'nmssm_available', 'mg5_version', 'model_path'
    """
    result = {
        "mg5_found": False,
        "nmssm_available": False,
        "mg5_version": None,
        "model_path": None,
    }

    # Check MG5 executable
    try:
        ver = subprocess.run(
            [mg5_executable, "--version"],
            capture_output=True, text=True, timeout=10
        )
        result["mg5_found"] = ver.returncode == 0
        result["mg5_version"] = ver.stdout.strip() or ver.stderr.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        result["mg5_found"] = False
        result["mg5_version"] = f"Error: {e}"
        return result

    # Check nmssm model path
    # Standard MG5 location: MG5_DIR/models/nmssm/
    try:
        mg5_dir = subprocess.run(
            [mg5_executable, "-c", "print(MG5DIR)"],
            capture_output=True, text=True, timeout=10
        )
        for line in mg5_dir.stdout.split("\n"):
            if "MG5DIR" in line or ("/" in line and "MG5" in line):
                mg5_dir_path = line.strip()
                model_path = Path(mg5_dir_path) / "models" / "nmssm"
                if model_path.exists():
                    result["nmssm_available"] = True
                    result["model_path"] = str(model_path)
    except Exception:
        pass

    # Fallback: try to find nmssm model via common paths
    for candidate in [
        "/usr/local/mg5_aMC/models/nmssm",
        os.path.expanduser("~/MG5_aMC/models/nmssm"),
        "/opt/mg5/models/nmssm",
    ]:
        if Path(candidate).exists():
            result["nmssm_available"] = True
            result["model_path"] = candidate
            break

    return result


if __name__ == "__main__":
    mg5_exec = sys.argv[1] if len(sys.argv) > 1 else "mg5_aMC"
    print(f"Checking MG5 nmssm model availability (executable: {mg5_exec})")
    status = check_mg5_nmssm(mg5_exec)
    for k, v in status.items():
        print(f"  {k}: {v}")
    if status["nmssm_available"]:
        print("\nOK: nmssm model available — ready to run run_mg5_production.py")
    else:
        print("\nFAIL: nmssm model not found — check MG5 installation")
        sys.exit(1)
