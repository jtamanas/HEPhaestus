"""should_invoke_class.py — Step 6 trigger helper (D11 / §4.1).

Determines whether the /class side-check should be invoked based on the
runner spec's ``cosmology`` block.

Usage as a module::

    from should_invoke_class import should_invoke_class
    result = should_invoke_class(spec)  # True or False

Usage as a CLI::

    python -m dark-matter-constraints.scripts.should_invoke_class spec.yaml
    # prints "true" or "false" to stdout
"""
from __future__ import annotations

import json
import sys
import pathlib


def should_invoke_class(spec: dict) -> bool:
    """Return True iff the runner spec requests a non-standard cosmology run.

    Logic verbatim from design §4.1::

        cosmology = spec.get("cosmology")
        if cosmology is None:
            return False
        if isinstance(cosmology, str):  # legacy scalar form
            return cosmology != "standard_thermal"
        if isinstance(cosmology, dict):
            return cosmology.get("kind", "standard_thermal") != "standard_thermal"
        return False  # malformed — caught by RUNNER_SPEC_INVALID

    Parameters
    ----------
    spec:
        Loaded (and normalised) runner-spec dict.

    Returns
    -------
    bool
        True if /class should be invoked; False otherwise.
    """
    cosmology = spec.get("cosmology")
    if cosmology is None:
        return False
    if isinstance(cosmology, str):  # legacy scalar form
        return cosmology != "standard_thermal"
    if isinstance(cosmology, dict):
        return cosmology.get("kind", "standard_thermal") != "standard_thermal"
    return False  # malformed — caught by RUNNER_SPEC_INVALID


# ---------------------------------------------------------------------------
# CLI wrapper — prints "true" / "false" to stdout
# ---------------------------------------------------------------------------

def _main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python should_invoke_class.py <spec_yaml>",
            file=sys.stderr,
        )
        sys.exit(1)

    spec_path = pathlib.Path(sys.argv[1])

    # Import loader; fall back to plain yaml if shared loader not on path
    try:
        import importlib.util as _ilu
        _loader_path = pathlib.Path(__file__).resolve().parents[4] / "shared" / "runner_spec_loader.py"
        _spec_m = _ilu.spec_from_file_location("runner_spec_loader", _loader_path)
        _mod = _ilu.module_from_spec(_spec_m)
        _spec_m.loader.exec_module(_mod)
        spec = _mod.load_runner_spec(spec_path)
    except Exception:
        import yaml
        with open(spec_path) as fh:
            spec = yaml.safe_load(fh) or {}

    result = should_invoke_class(spec)
    print("true" if result else "false")


if __name__ == "__main__":
    _main()
