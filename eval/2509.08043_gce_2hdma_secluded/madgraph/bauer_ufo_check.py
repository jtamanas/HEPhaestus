"""
Bauer UFO parameter-name assertion check.
arXiv:2509.08043, Section 3.2.6 (BL7 bound — vendored stub route 2).

Loads stub_ufo/parameters.py via importlib.util.spec_from_file_location
(no dotted import, no sys.path.insert — avoids collision with any other
`parameters` module already in sys.modules).

Usage:
    python eval/2509.08043_gce_2hdma_secluded/madgraph/bauer_ufo_check.py

Exits 0 on success (EXPECTED_PARAMS subset of stub params).
Exits 1 on failure with an explanatory message.
"""

import importlib.util
import hashlib
import os
import sys
from pathlib import Path


def _load_stub_ufo(ufo_dir: str = None) -> object:
    """Load stub_ufo/parameters.py via importlib.util (no dotted import).

    Parameters
    ----------
    ufo_dir : str, optional
        Path to directory containing parameters.py.
        Defaults to the stub_ufo/ directory adjacent to this script.

    Returns
    -------
    module : the loaded parameters module
    """
    if ufo_dir is None:
        ufo_dir = Path(__file__).parent / "stub_ufo"
    params_path = Path(ufo_dir) / "parameters.py"

    if not params_path.exists():
        raise FileNotFoundError(
            f"UFO parameters file not found at: {params_path}\n"
            f"Expected the vendored stub at madgraph/stub_ufo/parameters.py"
        )

    spec = importlib.util.spec_from_file_location(
        "bauer_ufo_stub_parameters",  # unique module name to avoid sys.modules collision
        str(params_path),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_of_file(path: str) -> str:
    """Return hex SHA-256 digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def verify_ufo(ufo_dir: str = None, ufo_tarball: str = None) -> dict:
    """Verify that EXPECTED_PARAMS are present in the stub UFO parameter list.

    Uses importlib.util.spec_from_file_location — does NOT shell out to mg5_aMC.
    Safe to run in CI without MadGraph5 installed.

    Parameters
    ----------
    ufo_dir : str, optional
        Directory containing parameters.py. Defaults to stub_ufo/ next to this script.
    ufo_tarball : str, optional
        If given, compute SHA-256 of this file and compare to PINNED_SHA.

    Returns
    -------
    dict with keys:
        found_params     : frozenset of parameter names found in the stub
        expected_params  : EXPECTED_PARAMS frozenset
        missing          : expected - found (should be empty)
        sha256           : SHA-256 of parameters.py (or None if not requested)
        ok               : bool — True iff missing is empty
    """
    # Load EXPECTED_PARAMS from the sibling expected_ufo_params.py
    expected_path = Path(__file__).parent / "expected_ufo_params.py"
    expected_spec = importlib.util.spec_from_file_location(
        "bauer_ufo_expected_params",
        str(expected_path),
    )
    expected_module = importlib.util.module_from_spec(expected_spec)
    expected_spec.loader.exec_module(expected_module)
    EXPECTED_PARAMS = expected_module.EXPECTED_PARAMS

    # Load the stub UFO
    stub_module = _load_stub_ufo(ufo_dir)
    found_params = frozenset(p.name for p in stub_module.all_parameters)

    missing = EXPECTED_PARAMS - found_params

    # Optional SHA-256 check
    sha = None
    if ufo_tarball is not None:
        sha = sha256_of_file(ufo_tarball)
        pinned = getattr(expected_module, "PINNED_SHA", None)
        if pinned and pinned != "placeholder-computed-post-commit":
            if sha != pinned:
                return {
                    "found_params": found_params,
                    "expected_params": EXPECTED_PARAMS,
                    "missing": missing,
                    "sha256": sha,
                    "ok": False,
                    "error": f"SHA-256 mismatch: got {sha}, expected {pinned}",
                }

    return {
        "found_params": found_params,
        "expected_params": EXPECTED_PARAMS,
        "missing": missing,
        "sha256": sha,
        "ok": len(missing) == 0,
    }


if __name__ == "__main__":
    result = verify_ufo()
    if result["ok"]:
        print("OK: All expected UFO parameters found in vendored stub.")
        print(f"  Found : {sorted(result['found_params'])}")
        print(f"  Expected (subset): {sorted(result['expected_params'])}")
        sys.exit(0)
    else:
        print("FAIL: Missing parameters in UFO stub.")
        print(f"  Missing: {sorted(result['missing'])}")
        print(f"  Found  : {sorted(result['found_params'])}")
        sys.exit(1)
