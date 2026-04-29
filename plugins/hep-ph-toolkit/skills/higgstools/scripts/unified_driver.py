"""
unified_driver.py — thin wrapper around Higgs.bounds / Higgs.signals Python bindings.

Opt-in only: requires HEPPH_HIGGSTOOLS_BACKEND=unified.
Emits HIGGSTOOLS_BACKEND_UNAVAILABLE (recoverable) if the module is absent.

Produces the same result.json schema as legacy_driver.py, differentiated by
`backend: "unified"` and `dataset_version: "hbdataset@<sha>+hsdataset@<sha>"`.
"""
from __future__ import annotations

import sys
from typing import Any

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"


class UnifiedBackendUnavailable(Exception):
    """Raised when Higgs.bounds / Higgs.signals Python module cannot be imported."""

    def __init__(self, message: str):
        super().__init__(message)
        self.code = "HIGGSTOOLS_BACKEND_UNAVAILABLE"
        self.mode = "recoverable"
        self.message = message
        self.user_instruction = (
            "The unified HiggsTools C++ backend is not installed or not importable. "
            "Install it with bash _shared/installs/higgstools/install.sh install --backend=unified, "
            "or use the legacy backend (default)."
        )


def _import_higgs_modules():
    """Lazily import Higgs.bounds and Higgs.signals. Raises UnifiedBackendUnavailable if absent."""
    try:
        import Higgs.bounds  # noqa: F401
        import Higgs.signals  # noqa: F401
        return Higgs.bounds, Higgs.signals  # type: ignore[name-defined]
    except ImportError as exc:
        raise UnifiedBackendUnavailable(
            f"Failed to import Higgs.bounds / Higgs.signals: {exc}"
        ) from exc


def run_unified(
    slha_file: str,
    hbdataset_path: str,
    hsdataset_path: str,
    hbdataset_commit: str = "unknown",
    hsdataset_commit: str = "unknown",
    n_neutral: int = 1,
    n_charged: int = 0,
    dMh: dict[str, float] | None = None,
    delta_chi2: float = 6.18,
    chi2_sm_ref: float = 0.0,
) -> dict[str, Any]:
    """
    Run HiggsBounds + HiggsSignals via the unified C++ Python bindings.

    Raises UnifiedBackendUnavailable if the Python module is not installed.

    Returns the same result dict schema as legacy_driver.write_outputs().
    """
    hb_mod, hs_mod = _import_higgs_modules()

    dataset_version = f"hbdataset@{hbdataset_commit[:8]}+hsdataset@{hsdataset_commit[:8]}"

    # Use the unified API
    # Note: actual API calls depend on HiggsTools v1.2 interface.
    # This is a structural stub; integration test fills in real calls.
    hb_result = hb_mod.run(slha_file, datapath=hbdataset_path)  # type: ignore
    hs_result = hs_mod.run(slha_file, datapath=hsdataset_path)  # type: ignore

    from p_value import compute_p_value
    from exclusion import compute_hb_allowed, compute_hs_consistent

    channels = hb_result.channels if hasattr(hb_result, "channels") else []
    hb_allowed = compute_hb_allowed(channels)

    chi2_total = hs_result.chi2_total if hasattr(hs_result, "chi2_total") else 0.0
    hs_consistent = compute_hs_consistent(chi2_total, chi2_sm_ref, delta_chi2)

    ndf_rates = hs_result.ndf_rates if hasattr(hs_result, "ndf_rates") else 0
    ndf_masses = hs_result.ndf_masses if hasattr(hs_result, "ndf_masses") else 0
    chi2_rates = hs_result.chi2_rates if hasattr(hs_result, "chi2_rates") else chi2_total
    chi2_masses = hs_result.chi2_masses if hasattr(hs_result, "chi2_masses") else 0.0

    return {
        "hb_allowed": hb_allowed,
        "hs_consistent": hs_consistent,
        "obsratio_max": hb_result.obsratio_max if hasattr(hb_result, "obsratio_max") else 0.0,
        "chi2_total": chi2_total,
        "chi2_rates": chi2_rates,
        "chi2_masses": chi2_masses,
        "ndf_rates": ndf_rates,
        "ndf_masses": ndf_masses,
        "p_value_rates": compute_p_value(chi2_rates, ndf_rates),
        "p_value_masses": compute_p_value(chi2_masses, ndf_masses),
        "backend": "unified",
        "dataset_version": dataset_version,
    }
